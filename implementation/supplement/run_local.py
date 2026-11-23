"""Additional local experiments. Run from implementation or by absolute path."""
import json
import sqlite3
import sys
import tempfile
import threading
from itertools import permutations
from contextlib import closing
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from run_experiments import ISSUE, PILOT, bounded, rollback_check
from monitor import Config, Monitor, ToolAgent
from oracle import Oracle

READY = [*ISSUE, ('Reserve', 1), ('Submit', 1)]
JOB_OPS = ('Reserve', 'Submit', 'Commit', 'CancelConfirmed')


def checked(sut, oracle, state, command):
    expected, target = oracle.step(state, command)
    op = command[0]
    if op in JOB_OPS:
        observed, reason = ToolAgent(sut.config.owners[command[1]], sut).request(*command)
    else:
        observed, reason = sut.apply(command)
    actual = sut.snapshot()
    assert observed == expected and actual == oracle.wire(target), (command, actual, target)
    assert not oracle.requirements(actual, oracle.wire(state), command, observed)
    return target, dict(command=command, accepted=observed, reason=reason, state=actual)


def trace(config, commands):
    sut, oracle = Monitor(config), Oracle(config)
    state = oracle.initial
    rows = []
    try:
        for command in commands:
            state, row = checked(sut, oracle, state, command)
            rows.append(row)
    finally:
        sut.close()
    return rows


def cross_branch():
    config = Config((None, 0, 1, 1, 0), (2, 4, 4), (2, 1, 1), 2)
    commands = [*ISSUE, ('Delegate', 4, 1), ('Reserve', 0), ('Submit', 0),
                ('Reserve', 1), ('Revoke', 1), ('Commit', 0), ('Reserve', 2),
                ('CancelConfirmed', 0), ('Reserve', 2)]
    rows = trace(config, commands)
    assert rows[7]['state']['auth'] == [3, 0, 0, 0, 1]
    assert rows[7]['state']['pending'] == [0, 1]
    assert rows[7]['state']['used'] == 2
    assert [r['accepted'] for r in rows[8:]] == [False, False, True, True]
    assert rows[8]['state']['effects'] == [0, 0, 0]
    return rows


def convergent_prefixes():
    a, b, c = ISSUE
    left, right = [a, b, c], [a, c, b]
    suffix = [('Reserve', 1), ('Submit', 1), ('Commit', 1), ('Reserve', 2),
              ('Revoke', 1), ('Submit', 2), ('CancelConfirmed', 2)]
    first, second = (trace(PILOT, [*prefix, *suffix]) for prefix in (left, right))
    assert first[2]['state'] == second[2]['state'] and first[3:] == second[3:]
    return dict(prefixes=[left, right], common_suffix=first[3:])


class OrderedLock:
    """Force the commands' lock-entry order while all callers are pending."""
    def __init__(self, order, monitor_lock):
        self.order = order
        self.monitor_lock = monitor_lock
        self.condition = threading.Condition()
        self.local = threading.local()
        self.entries = []
        self.finished = 0

    def __enter__(self):
        with self.condition:
            assert self.condition.wait_for(
                lambda: self.local.call == self.order[self.finished], timeout=10)
            self.monitor_lock.acquire()
            self.entries.append(self.local.call)

    def __exit__(self, *exc):
        with self.condition:
            self.monitor_lock.release()
            self.finished += 1
            self.condition.notify_all()


def schedules():
    groups = [
        ('commit_commit', [('Commit', 1), ('Commit', 1)]),
        ('commit_cancel', [('Commit', 1), ('CancelConfirmed', 1)]),
        ('revoke_commit_cancel', [('Revoke', 1), ('Commit', 1), ('CancelConfirmed', 1)]),
    ]
    rows = []
    for name, commands in groups:
        for order in permutations(range(len(commands))):
            sut, oracle = Monitor(PILOT), Oracle(PILOT)
            state = oracle.initial
            try:
                for command in READY:
                    state, _ = checked(sut, oracle, state, command)
                original_lock = sut.lock
                lock = OrderedLock(order, original_lock)
                sut.lock = lock
                barrier = threading.Barrier(len(commands))

                def worker(call):
                    lock.local.call = call
                    barrier.wait(timeout=10)
                    return sut.apply(commands[call])[0]

                with ThreadPoolExecutor(max_workers=len(commands)) as pool:
                    futures = [pool.submit(worker, call) for call in range(len(commands))]
                    actual = [future.result(timeout=15) for future in futures]
                sut.lock = original_lock
                assert tuple(lock.entries) == order
                for call in lock.entries:
                    expected, state = oracle.step(state, commands[call])
                    assert actual[call] == expected
                final = sut.snapshot()
                assert final == oracle.wire(state)
                assert not oracle.requirements(final)
                assert sut.db.execute('SELECT count(*) FROM release_registry').fetchone()[0] == final['effects'][1]
                rows.append(dict(group=name, command_order=[commands[i] for i in order],
                                 caller_order=order, decisions=[actual[i] for i in order], final=final))
            finally:
                sut.close()
    return rows


def late_rollback():
    with tempfile.TemporaryDirectory() as folder:
        database = str(Path(folder) / 'monitor.sqlite')
        sut, oracle = Monitor(PILOT, database=database), Oracle(PILOT)
        state = oracle.initial
        try:
            for command in READY:
                state, _ = checked(sut, oracle, state, command)
            with closing(sqlite3.connect(database)) as observer:
                def snapshot():
                    tables = ('obligations', 'quota', 'jobs', 'release_registry', 'tool_effects', 'audit')
                    return {table: observer.execute(f'SELECT * FROM {table}').fetchall() for table in tables}
                before = snapshot()
                sut.db.execute("""
                    CREATE TRIGGER late_failure AFTER INSERT ON audit
                    WHEN NEW.operation = 'Commit'
                    BEGIN SELECT RAISE(ABORT, 'injected after effect and ledger'); END
                """)
                try:
                    sut.apply(('Commit', 1))
                except sqlite3.IntegrityError as error:
                    assert str(error) == 'injected after effect and ledger'
                else:
                    raise AssertionError('Missing injected failure')
                assert snapshot() == before and sut.snapshot() == oracle.wire(state)
                sut.db.execute('DROP TRIGGER late_failure')
                state, retry = checked(sut, oracle, state, ('Commit', 1))
                _, duplicate = checked(sut, oracle, state, ('Commit', 1))
                assert retry['accepted'] and not duplicate['accepted']
                after = snapshot()
                assert len(after['release_registry']) == len(after['tool_effects']) == 1
                assert not after['obligations']
                return dict(persistent_state_unchanged=True, retry=retry, duplicate=duplicate,
                            persisted_tool_effects=after['tool_effects'], persisted_releases=after['release_registry'])
        finally:
            sut.close()


if __name__ == '__main__':
    results = dict(pilot=bounded(PILOT, 'pilot_budget2'),
                   cross_branch=cross_branch(), convergent_prefixes=convergent_prefixes(),
                   schedules=schedules(), rollback_early=rollback_check(), rollback_late=late_rollback(),
                   root_revocation=trace(PILOT, [*READY, ('Revoke', 0), ('Commit', 1), ('CancelConfirmed', 1)]))
    (Path(__file__).resolve().parent / 'local_results.json').write_text(
        json.dumps(results, indent=2) + '\n')
    print(results['pilot'])
    print(f"Checked {len(results['schedules'])} forced caller orders")
