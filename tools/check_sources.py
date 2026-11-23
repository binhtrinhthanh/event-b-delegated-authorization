#!/usr/bin/env python3
"""Structural XML and reference checks only; native Rodin checks separately."""
from pathlib import Path
import xml.etree.ElementTree as ET
import json
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'DelegatedAuthorization';P='org.eventb.core.'
spec=json.loads((BASE/'model_spec.json').read_text());checked=[]
for m in spec['models']:
    path=OUT/(m['name']+'.bum');root=ET.parse(path).getroot()
    assert root.tag==P+'machineFile'
    assert [x.get(P+'identifier') for x in root.findall(P+'variable')]==m['variables']
    labels=[x.get(P+'label') for x in root.findall(P+'invariant')];assert len(labels)==len(set(labels))
    if m['ref']:
        assert root.find(P+'refinesMachine').get(P+'target')==m['ref']
        abstract=next(x for x in spec['models'] if x['name']==m['ref'])
    for e in root.findall(P+'event'):
        label=e.get(P+'label');expected=next(x for x in m['events'] if x['name']==label)
        assert [x.get(P+'predicate') for x in e.findall(P+'guard')]==expected['guards']
        assert [x.get(P+'assignment') for x in e.findall(P+'action')]==expected['actions']
        assert [x.get(P+'identifier') for x in e.findall(P+'parameter')]==expected['params']
        if expected['ref']:
            a=next(x for x in abstract['events'] if x['name']==expected['ref'])
            assert set(a['params'])<=set(expected['params'])
        for k,g in enumerate(e.findall(P+'guard')):assert g.get(P+'theorem')==('true' if k in expected.get('theorem_guards',[]) else 'false')
        assert len(e.findall(P+'action'))>0
    checked.append(path.name)
for name in ['C_Delegation.buc','C_Pilot.buc']:
    root=ET.parse(OUT/name).getroot();assert root.tag==P+'contextFile';checked.append(name)
assert ET.parse(OUT/'.project').getroot().find('name').text=='DelegatedAuthorization'
report={'method':'XML/structural checks; not Event-B parsing or type-checking','status':'PASS','components':checked}
(BASE/'validation/source_checks.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
