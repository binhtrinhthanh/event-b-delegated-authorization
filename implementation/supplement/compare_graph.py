"""Compare a normalized ProB state graph with the Python specification."""
from collections import defaultdict, deque
from pathlib import Path
import json
import re
import sys

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from run_experiments import PILOT
from monitor import Config
from oracle import Oracle

P = 'org.eventb.core.'
SOURCE = HERE.parent.parent / 'DelegatedAuthorization'
CONFIGS = {
    'chain_budget1': Config((None, 0, 1), (1, 2), (1, 2), 1),
    'star_budget2': Config((None, 0, 0), (1, 2), (1, 2), 2),
    'pilot_budget2': PILOT,
}

def parse_graph(text, config):
    states, edges = {}, defaultdict(dict)
    initial = None
    text = text.replace(r'\n', '').replace('\\', '')
    node_count, job_count = len(config.parents), len(config.owners)

    def get_set(label, variable):
        match = re.search(rf'\b{variable} = \{{([^}}]*)\}}', label)
        assert match, (variable, label)
        return match[1]

    def masks(label, variable):
        values = [0] * node_count
        for node, cap in re.findall(r'\(n(\d+)\|->(readCap|writeCap)\)', get_set(label, variable)):
            values[int(node)] |= 1 if cap == 'readCap' else 2
        return values

    for line in text.splitlines():
        match = re.match(r'(\d+)(?: -> (\d+))? \[.*?label="([^"]*)"', line)
        if not match:
            continue
        source, target, label = match.groups()
        if label == 'INITIALISATION':
            assert initial is None
            initial = int(target)
        elif target is not None:
            op, arg = re.match(r'(\w+)\([nj](\d+)[,)]', label).groups()
            command = (op, int(arg))
            if op == 'Delegate':
                scope = re.match(r'Delegate\(n\d+,\{([^}]*)\},', label)[1]
                command += (int('readCap' in scope) + 2 * int('writeCap' in scope),)
            existing = edges[int(source)].setdefault(command, int(target))
            assert existing == int(target), (label, command)
        elif 'badUse' in label:
            phases = [0] * job_count
            pending = []
            for phase, variable in enumerate(('pending', 'submitted', 'committed', 'cancelled'), 1):
                indices = sorted(int(value) for value in re.findall(r'j(\d+)', get_set(label, variable)))
                for index in indices:
                    phases[index] = phase
                if phase == 1:
                    pending = indices
            effects = dict((int(i), int(count)) for i, count in re.findall(r'effectCount\(j(\d+)\) = (\d+)', label))
            used = int(re.search(r'\bused = (\d+)', label)[1])
            revoked = set(re.findall(r'n(\d+)', get_set(label, 'revoked')))
            scopes = masks(label, 'scope')
            assert get_set(label, 'issued').split(',') == [
                f'n{i}' for i, scope in enumerate(scopes) if scope
            ]
            assert 'badUse = FALSE' in label
            states[int(source)] = dict(scopes=scopes, auth=masks(label, 'auth'), phases=phases,
                                       pending=pending, effects=[effects[i] for i in range(job_count)],
                                       used=used, revoked=[str(i) in revoked for i in range(node_count)])
    assert initial is not None and initial in states
    return initial, states, edges


def compare_graph(config, text):
    initial, states, edges = parse_graph(text, config)
    oracle = Oracle(config)
    queue = deque([(initial, oracle.initial)])
    seen = {initial: oracle.initial}
    counts = defaultdict(int)
    commands = list(oracle.commands())
    while queue:
        node, state = queue.popleft()
        assert oracle.wire(state) == states[node], (node, oracle.wire(state), states[node])
        observed = set(edges[node])
        for command in commands:
            enabled, target = oracle.step(state, command)
            counts['candidate_commands'] += 1
            assert enabled == (command in observed), (node, command, enabled, observed)
            if enabled:
                target_node = edges[node][command]
                assert oracle.wire(target) == states[target_node], (node, command, target_node)
                counts['enabled_transitions'] += 1
                if target_node in seen:
                    assert seen[target_node] == target
                else:
                    seen[target_node] = target
                    queue.append((target_node, target))
        assert not observed - set(commands)
    assert len(seen) == len(states) == len(set(seen.values()))
    witnesses = {}
    if config == PILOT:
        for label, outcome in (
            ('authorized_commit', [('Commit', 1, True)]),
            ('blocked_then_cancelled', [('Revoke', 1, True), ('Commit', 1, False),
                                       ('CancelConfirmed', 1, True)]),
        ):
            prefix = [('Delegate', 1, 3), ('Delegate', 2, 2), ('Reserve', 1), ('Submit', 1)]
            node = initial
            trace = []
            for *args, accepted in [(*cmd, True) for cmd in prefix] + outcome:
                command = tuple(args)
                assert (command in edges[node]) == accepted
                if accepted:
                    node = edges[node][command]
                trace.append(dict(command=command, accepted=accepted, state=states[node]))
            witnesses[label] = trace
    return dict(states=len(states), mismatches=0, **counts, witnesses=witnesses)


