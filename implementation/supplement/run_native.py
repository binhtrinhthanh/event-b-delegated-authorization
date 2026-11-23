"""Export and explore native Event-B using the ProB2 API and ProB CLI."""
import argparse
import gzip
import json
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import xml.etree.ElementTree as ET

from compare_graph import CONFIGS, HERE, P, PILOT, SOURCE, compare_graph


def instantiate(project, config):
    if config == PILOT:
        return
    parent2 = ('u', 'a1')[config.parents[2]]
    predicates = {
        'pilot01': 'partition(NODE,{u},{a1},{a2})',
        'pilot03': 'partition(JOB,{req1},{req2})',
        'pilot06': 'parent={a1 ↦ u,a2 ↦ ' + parent2 + '}',
        'pilot07': 'rank={u ↦ 0,a1 ↦ 1,a2 ↦ ' + str(int(parent2 == 'a1') + 1) + '}',
        'pilot08': 'path={u ↦ {u},a1 ↦ {u,a1},a2 ↦ {' +
                   ('u,a1,a2' if parent2 == 'a1' else 'u,a2') + '}}',
        'pilot09': 'owner={req1 ↦ a1,req2 ↦ a2}',
        'pilot10': 'need={req1 ↦ readCap,req2 ↦ writeCap}',
        'pilot11': f'budget={config.budget}',
    }
    for filename in ('C_Pilot.bcc', 'M3_Pilot.bcm'):
        file = project / filename
        tree = ET.parse(file)
        context = tree.getroot()
        if filename.endswith('.bcm'):
            context = next(el for el in context.findall(P + 'scInternalContext')
                           if el.get('name') == 'C_Pilot')
        for axiom in context.findall(P + 'scAxiom'):
            label = axiom.get(P + 'label')
            if label in predicates:
                axiom.set(P + 'predicate', predicates[label])
        for constant in context.findall(P + 'scConstant'):
            if constant.get('name') in ('a3', 'req3'):
                context.remove(constant)
        tree.write(file, encoding='UTF-8', xml_declaration=True)


def mutate(project, variant):
    # Mirror the existing .bum negative controls in the typed animation input.
    # Rodin proof status for these inputs is independent of this procedure.
    for name in ('M2_SubmittedObligations', 'M3_Pilot'):
        file = project / f'{name}.bcm'
        tree = ET.parse(file)
        root = tree.getroot()
        if variant == 'cached_authorization':
            commit = next(e for e in root.findall(P + 'scEvent') if e.get(P + 'label') == 'Commit')
            guard = next(g for g in commit.findall(P + 'scGuard')
                         if g.get(P + 'predicate') == 'owner(j) ↦ need(j)∈auth')
            commit.remove(guard)
        elif variant == 'early_release':
            event = ET.SubElement(root, P + 'scEvent', {
                'name': 'ReleaseUnconfirmed', P + 'label': 'ReleaseUnconfirmed',
                P + 'convergence': '1', P + 'extended': 'false', P + 'accurate': 'true',
            })
            if name == 'M3_Pilot':
                target = '/DelegatedAuthorization/M2_SubmittedObligations.bcm'
                target += '|org.eventb.core.scMachineFile#M2_SubmittedObligations'
                target += '|org.eventb.core.scEvent#ReleaseUnconfirmed'
                ET.SubElement(event, P + 'scRefinesEvent', {'name': 'ref', P + 'scTarget': target})
            ET.SubElement(event, P + 'scGuard', {'name': 'g', P + 'label': 'grd_mut',
                          P + 'predicate': 'j∈submitted', P + 'theorem': 'false'})
            ET.SubElement(event, P + 'scParameter', {'name': 'j', P + 'type': 'JOB'})
            for i, assignment in enumerate(('pending ≔ pending ∖ {j}', 'used ≔ used − 1')):
                ET.SubElement(event, P + 'scAction', {'name': f'a{i}', P + 'label': f'act{i}',
                              P + 'assignment': assignment})
        else:
            raise ValueError(variant)
        tree.write(file, encoding='UTF-8', xml_declaration=True)


def normalize_graph(text):
    text = text.replace(r'\n', '')
    names = {'u': 'n0', **{f'a{i}': f'n{i}' for i in range(1, 4)},
             **{f'req{i}': f'j{i-1}' for i in range(1, 4)}}
    text = re.sub(r'\b(u|a[1-3]|req[1-3])\b', lambda match: names[match[0]], text)
    # The native exporter orders Delegate parameters as (a,P,S).
    return re.sub(r'Delegate\((n\d+),(.*?),((?:\\\{)[^}]*?\\\})\)"',
                  lambda match: f'Delegate({match[1]},{match[3]},{match[2]})"', text)


def execute(args, config, folder, variant=None):
    folder.mkdir(parents=True, exist_ok=True)
    model_file = folder / 'model.eventb'
    with tempfile.TemporaryDirectory() as tmp:
        project = Path(tmp) / 'DelegatedAuthorization'
        shutil.copytree(SOURCE, project, ignore=shutil.ignore_patterns('*.bpo', '*.bpr', '*.bps'))
        instantiate(project, config)
        if variant:
            mutate(project, variant)
        with (folder / 'export.log').open('w') as log:
            subprocess.run([args.java, '-cp', str(args.prob2_jar), 'groovy.ui.GroovyMain',
                            str(HERE / 'export.groovy'), str(project / 'M3_Pilot.bcm'), str(model_file)],
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=120)
    command = [str(args.probcli), str(model_file), '-model_check', '-nodead',
               '-p', 'MAX_OPERATIONS', '1000']
    graph = folder / 'graph.dot'
    trace = folder / 'trace.json'
    def invoke(options, name):
        result = subprocess.run(command + options, text=True, stdout=subprocess.PIPE,
                                stderr=subprocess.STDOUT, timeout=180, check=True)
        (folder / name).write_text(result.stdout)
        return result.stdout

    def trace_options(path):
        return ['-bf', '-his', str(path), '-his_option', 'json', '-his_option', 'show_states']

    if variant:
        full_result = invoke(trace_options(trace), 'prob.log')
        assert '*** COUNTER EXAMPLE FOUND ***' in full_result and trace.stat().st_size, full_result
        diagnostics = set(re.findall(r'^event_error:[^\n]+', full_result, re.MULTILINE))
        if 'invariant_violation' in full_result:
            diagnostics.add('invariant_violation')
        assert diagnostics, full_result
        violation = {'cached_authorization': 'badUse = TRUE',
                     'early_release': 'not(submitted <: pending)'}[variant]
        goal_trace = folder / 'concrete_goal_trace.json'
        concrete_result = invoke(['-p', 'NUMBER_OF_ANIMATED_ABSTRACTIONS', '0',
                                  '-p', 'PROOF_INFO', 'false', '-goal', violation] +
                                 trace_options(goal_trace), 'concrete_goal.log')
        assert 'goal_found' in concrete_result and goal_trace.stat().st_size, concrete_result
        return dict(variant=variant, full_hierarchy=sorted(diagnostics), reached_violation=violation)


    result = invoke(['-dot', 'state_space', str(graph)], 'prob.log')
    assert 'No counter example found. ALL states visited.' in result, result
    raw = graph.read_text()
    summary = compare_graph(config, normalize_graph(raw))
    with gzip.open(folder / 'graph.dot.gz', 'wt') as zipped:
        zipped.write(raw)
    graph.unlink()
    return summary


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('probcli', type=lambda s: Path(s).resolve())
    parser.add_argument('prob2_jar', type=lambda s: Path(s).resolve())
    parser.add_argument('--java', default='java')
    parser.add_argument('--only', choices=(*CONFIGS, 'cached_authorization', 'early_release'))
    args = parser.parse_args()
    output = HERE / 'native_results'
    report = {}
    for name in (*CONFIGS, 'cached_authorization', 'early_release'):
        if args.only and args.only != name:
            continue
        report[name] = execute(args, CONFIGS.get(name, PILOT), output / name,
                               None if name in CONFIGS else name)
        print(name, {k: v for k, v in report[name].items() if k != 'witnesses'}, flush=True)
    destination = output / (f'{args.only}_summary.json' if args.only else 'summary.json')
    destination.write_text(json.dumps(report, indent=2) + '\n')
