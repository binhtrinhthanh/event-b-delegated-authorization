"""Differential checks on selected traces of a deeper delegation tree."""
import json
from pathlib import Path

from run_local import Config, trace

CONFIG = Config((None, 0, 1, 2, 0, 4, 5), (1, 2, 3, 4, 5, 6),
                (1, 2, 1, 2, 1, 2), 3)
ISSUE = [('Delegate', actor, 3) for actor in range(1, 7)]
rows = []
for ancestors, leaf, other in (((1, 2, 3), 2, (3, 4, 5)),
                               ((4, 5, 6), 5, (0, 1, 2))):
    first, second, waiting = other
    for revoked in ancestors:
        setup = [*ISSUE, ('Reserve', leaf), ('Submit', leaf)]
        for commit_first in (False, True):
            if commit_first:
                commands = [*setup, ('Commit', leaf), ('Revoke', revoked), ('Commit', leaf)]
                expected = [True] * (len(commands) - 1) + [False]
            else:
                commands = [*setup, ('Reserve', first), ('Reserve', second),
                            ('Revoke', revoked), ('Commit', leaf), ('Reserve', waiting),
                            ('CancelConfirmed', leaf), ('Reserve', waiting)]
                expected = [True] * (len(commands) - 4) + [False, False, True, True]
            events = trace(CONFIG, commands)
            assert [r['accepted'] for r in events] == expected
            final = events[-1]['state']
            assert final['effects'][leaf] == int(commit_first)
            if not commit_first:
                assert events[-4]['state']['used'] == 3
                assert leaf in events[-4]['state']['pending']
                assert final['used'] == 3 and waiting in final['pending']
            rows.append(dict(revoked=revoked, job=leaf, commit_first=commit_first, events=events))

result = dict(configuration=dict(parents=CONFIG.parents, owners=CONFIG.owners,
                                 needs=CONFIG.needs, budget=CONFIG.budget, capabilities=2),
              traces=len(rows), command_trials=sum(len(row['events']) for row in rows),
              accepted=sum(e['accepted'] for row in rows for e in row['events']),
              mismatches=0, evidence=rows)
Path('deep_branches_results.json').write_text(json.dumps(result, indent=2) + '\n')
print({k:v for k,v in result.items() if k != 'evidence'})
