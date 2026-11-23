#!/usr/bin/env python3
"""Native negative controls: mutate concrete M2 while retaining all requirements.
Open POs are diagnostic evidence, not by themselves a counterexample.
Implementation scenario witnesses are reported separately.
"""
from pathlib import Path
import argparse,copy,json,shutil,subprocess,sys,tempfile,xml.etree.ElementTree as E
BASE=Path(__file__).resolve().parents[1];OUT=BASE/'implementation/model_mutants';P='org.eventb.core.'
NAMES=['scope_expansion','local_revocation','cached_authorization','no_shared_budget','early_release','replay_commit']

def event(root,label):return next(e for e in root.findall(P+'event') if e.get(P+'label')==label)
def remove_guard(root,label,predicate):
    e=event(root,label);gs=[g for g in e.findall(P+'guard') if g.get(P+'predicate')==predicate]
    assert len(gs)==1,(label,predicate);e.remove(gs[0])
def new_event(root,label,guard,assignments,refinement=False):
    e=E.SubElement(root,P+'event',{'name':'mutation'+label,P+'label':label,P+'convergence':'1',P+'extended':'false'})
    if refinement:E.SubElement(e,P+'refinesEvent',{'name':'ref',P+'target':label})
    E.SubElement(e,P+'parameter',{'name':'j',P+'identifier':'j'})
    E.SubElement(e,P+'guard',{'name':'g',P+'label':'grd_mut',P+'predicate':guard,P+'theorem':'false'})
    for i,a in enumerate(assignments):E.SubElement(e,P+'action',{'name':f'a{i}',P+'label':f'act_mut{i}',P+'assignment':a})

def generate(name):
    target=OUT/name/'DelegatedAuthorization';target.mkdir(parents=True,exist_ok=True)
    for f in (BASE/'DelegatedAuthorization').iterdir():
        if f.suffix in ('.bum','.buc') or f.name=='.project':shutil.copy2(f,target/f.name)
    for level in ('M2_SubmittedObligations','M3_Pilot'):
        path=target/(level+'.bum');tree=E.parse(path);root=tree.getroot()
        before=[E.tostring(x,encoding='unicode') for x in root.findall(P+'invariant')]
        if name=='scope_expansion':remove_guard(root,'Delegate','S ⊆ scope[{parent(a)}]')
        elif name=='local_revocation':
            gs=event(root,'Revoke').findall(P+'guard');changed=0
            for g in gs:
                text=g.get(P+'predicate')
                if 'path(x) ∩ (revoked ∪ {a}) = ∅' in text:
                    g.set(P+'predicate',text.replace('path(x) ∩ (revoked ∪ {a}) = ∅','x ∉ (revoked ∪ {a})'));changed+=1
            assert changed==1
        elif name=='cached_authorization':remove_guard(root,'Commit','owner(j) ↦ need(j) ∈ auth')
        elif name=='no_shared_budget':remove_guard(root,'Reserve','used < budget')
        elif name=='early_release':new_event(root,'ReleaseUnconfirmed','j ∈ submitted',['pending ≔ pending ∖ {j}','used ≔ used − 1'],level=='M3_Pilot')
        elif name=='replay_commit':new_event(root,'ReplayCommit','j ∈ committed',['effectCount(j) ≔ effectCount(j) + 1'],level=='M3_Pilot')
        assert before==[E.tostring(x,encoding='unicode') for x in root.findall(P+'invariant')],'Requirements changed'
        E.indent(tree);tree.write(path,encoding='UTF-8',xml_declaration=True)
    for stem in ('C_Delegation.buc','C_Pilot.buc','M0_AuthorityLedger.bum','M1_DelegationChain.bum'):
        assert (target/stem).read_bytes()==(BASE/'DelegatedAuthorization'/stem).read_bytes()
    return target

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--rodin',required=True);parser.add_argument('--ecj');args=parser.parse_args()
    OUT.mkdir(exist_ok=True);work=Path(tempfile.mkdtemp(prefix='delegated-model-mutations-'));rows=[]
    for name in NAMES:
        source=generate(name);folder=OUT/name;log=folder/'native.log'
        command=[sys.executable,str(BASE/'tools/run_rodin.py'),'--rodin',args.rodin,'--work',str(work/name),'--source',str(source),'--log',str(log)]
        if args.ecj:command+=['--ecj',args.ecj]
        with (folder/'runner.log').open('w') as f:run=subprocess.run(command,stdout=f,stderr=subprocess.STDOUT,timeout=240)
        assert run.returncode==0,(name,'native process failed')
        text=log.read_text();assert 'STATIC_ERRORS 0' in text and 'NATIVE_BUILD_COMPLETE' in text,(name,'static or build failure')
        native=work/name/'workspace/DelegatedAuthorization';po=[];summary=[]
        for f in sorted(native.glob('*.bps')):
            statuses=E.parse(f).getroot().findall(P+'psStatus')
            opened=[r.get('name') for r in statuses if int(r.get(P+'confidence'))<1000]
            po.extend(dict(component=f.stem,po=p) for p in opened)
            summary.append(dict(component=f.stem,total=len(statuses),open=len(opened)))
        assert any(r['component']=='M2_SubmittedObligations' for r in po),(name,'mutation unexpectedly proved')
        # Save the generated PO goals so negative controls are inspectable in Rodin.
        shutil.copy2(native/'M2_SubmittedObligations.bpo',folder/'M2_SubmittedObligations.bpo')
        row=dict(mutant=name,static_errors=0,requirements_unchanged=True,open_pos=po,total_open=len(po),components=summary,status='EXPECTED_UNDISCHARGED_OBLIGATIONS')
        (folder/'summary.json').write_text(json.dumps(row,indent=2)+'\n');rows.append(row)
        print(json.dumps(dict(mutant=name,total_open=len(po),M2_open=[r['po'] for r in po if r['component']=='M2_SubmittedObligations'])),flush=True)
    (OUT/'native_mutation_summary.json').write_text(json.dumps(dict(method='Native Rodin negative controls with unchanged invariants; not native ProB counterexample generation.',mutants=rows),indent=2)+'\n')
if __name__=='__main__':main()
