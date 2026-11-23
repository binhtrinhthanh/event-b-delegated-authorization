"""Check each candidate after multiple distinct accepted histories per oracle state."""
import argparse
from collections import Counter, defaultdict, deque
from contextlib import closing
import json
from pathlib import Path
import time

from run_local import checked
from monitor import Config, Monitor
from oracle import Oracle

CONFIGS = {
    'chain_budget1': Config((None, 0, 1), (1, 2), (1, 2), 1),
    'star_budget2': Config((None, 0, 0), (1, 2), (1, 2), 2),
}


def histories(oracle, commands, limit):
    prefixes = defaultdict(list, {oracle.initial: [()]})
    queue = deque([(oracle.initial, ())])
    while queue:
        state, prefix = queue.popleft()
        for command in commands:
            accepted, successor = oracle.step(state, command)
            if accepted and len(prefixes[successor]) < limit:
                candidate = prefix + (command,)
                prefixes[successor].append(candidate)
                queue.append((successor, candidate))
    return prefixes


def assess(config, limit):
    start = time.perf_counter()
    oracle = Oracle(config)
    commands = tuple(oracle.commands())
    prefixes = histories(oracle, commands, limit)
    histogram = Counter(map(len, prefixes.values()))
    counts = Counter()
    for state, alternatives in prefixes.items():
        if len(alternatives) < 2:
            continue
        for prefix in alternatives:
            with closing(Monitor(config)) as monitor:
                current = oracle.initial
                try:
                    for command in prefix:
                        current, result = checked(monitor, oracle, current, command)
                        assert result['accepted']
                    assert current == state and monitor.snapshot() == oracle.wire(state)
                    for command in commands:
                        monitor.db.execute('SAVEPOINT trial')
                        try:
                            _, result = checked(monitor, oracle, state, command)
                            counts['accepted' if result['accepted'] else 'rejected'] += 1
                        finally:
                            monitor.db.execute('ROLLBACK TO trial')
                            monitor.db.execute('RELEASE trial')
                    assert monitor.snapshot() == oracle.wire(state)
                except AssertionError as error:
                    raise AssertionError((prefix, command, error.args)) from error
    tested_states = sum(n for k, n in histogram.items() if k >= 2)
    tested_prefixes = sum(k * n for k, n in histogram.items() if k >= 2)
    assert sum(counts.values()) == tested_prefixes * len(commands)
    return {
        'reachable_oracle_states': len(prefixes),
        'retained_prefix_histogram': dict(sorted(histogram.items())),
        'convergent_states_tested': tested_states,
        'prefixes_tested': tested_prefixes,
        'alternative_prefixes_beyond_first': tested_prefixes - tested_states,
        'candidate_commands_per_prefix': len(commands),
        'command_trials': sum(counts.values()),
        'accepted_trials': counts['accepted'],
        'rejected_trials': counts['rejected'],
        'mismatches': 0,
        'seconds': round(time.perf_counter() - start, 3),
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, default=Path(__file__).with_name('converging_histories_results.json'))
    args = parser.parse_args()
    limit = 8
    result = {'prefix_cap_per_state': limit, 'configurations': {}}
    for name, config in CONFIGS.items():
        result['configurations'][name] = assess(config, limit)
        print(name, result['configurations'][name], flush=True)
    args.output.write_text(json.dumps(result, indent=2) + '\n', encoding='utf-8')


if __name__ == '__main__':
    main()
