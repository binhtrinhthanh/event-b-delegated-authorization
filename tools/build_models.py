#!/usr/bin/env python3
"""Generate Rodin source XML and readable mathematical listings; no fake proofs."""
from pathlib import Path
import json
import xml.etree.ElementTree as ET
from copy import deepcopy
BASE=Path(__file__).resolve().parents[1]
OUT=BASE/'DelegatedAuthorization'
P='org.eventb.core.'
def element(parent,kind,name=None,**attrs):
    a={P+k:str(v) for k,v in attrs.items()}
    if name is not None:a={'name':name,**a}
    return ET.SubElement(parent,P+kind,a)
def write(root,path):
    ET.indent(root);ET.ElementTree(root).write(path,encoding='UTF-8',xml_declaration=True)
def auth(issued='issued',scope='scope',revoked='revoked'):
    # A relation between agents and capabilities; no function into powersets.
    return scope+' ∩ {x,k · x ∈ NODE ∧ k ∈ CAP ∧ path(x) ∩ '+revoked+' = ∅ ∣ x ↦ k}'
def ev(name,params=(),guards=(),actions=(),ref=None,convergent=False):
    return dict(name=name,params=list(params),guards=list(guards),actions=list(actions),ref=ref,convergent=convergent)
sets=['NODE','CAP','JOB']
constants=['root','rootScope','parent','rank','path','owner','need','budget']
axioms=[
('axm01','finite(NODE)'),('axm02','finite(CAP)'),('axm03','finite(JOB)'),
('axm04','root ∈ NODE'),('axm05','rootScope ⊆ CAP'),('axm06','rootScope ≠ ∅'),
('axm07','parent ∈ (NODE ∖ {root}) → NODE'),('axm08','rank ∈ NODE → ℕ'),('axm09','rank(root) = 0'),
('axm10','∀a · a ∈ NODE ∖ {root} ⇒ rank(parent(a)) < rank(a)'),
('axm11','path ∈ NODE → ℙ(NODE)'),('axm12','path(root) = {root}'),
('axm13','∀a · a ∈ NODE ∖ {root} ⇒ path(a) = {a} ∪ path(parent(a))'),
('axm14','owner ∈ JOB → (NODE ∖ {root})'),('axm15','need ∈ JOB → CAP'),('axm16','budget ∈ ℕ1')]
variables0=['auth','pending','committed','cancelled','used']
invariants0=[('inv01','auth ⊆ NODE × CAP'),('inv02','pending ⊆ JOB'),('inv02f','finite(pending)'),('inv03','committed ⊆ JOB'),('inv03f','finite(committed)'),('inv04','cancelled ⊆ JOB'),('inv05','pending ∩ committed = ∅'),('inv06','pending ∩ cancelled = ∅'),('inv07','committed ∩ cancelled = ∅'),('inv08','used ∈ ℕ'),('inv09','used = card(pending) + card(committed)'),('inv10','used ≤ budget')]
init0=['auth ≔ {root} × rootScope','pending ≔ ∅','committed ≔ ∅','cancelled ≔ ∅','used ≔ 0']
reserve=ev('Reserve',['j'],['j ∈ JOB ∖ (pending ∪ committed ∪ cancelled)','owner(j) ↦ need(j) ∈ auth','used < budget'],['pending ≔ pending ∪ {j}','used ≔ used + 1'])
commit=ev('Commit',['j'],['j ∈ pending','owner(j) ↦ need(j) ∈ auth'],['pending ≔ pending ∖ {j}','committed ≔ committed ∪ {j}'])
cancel=ev('CancelConfirmed',['j'],['j ∈ pending'],['pending ≔ pending ∖ {j}','cancelled ≔ cancelled ∪ {j}','used ≔ used − 1'])
# Expose the unique remainder as an event parameter. The partition facts are
# theorem guards: they must be proved and do not strengthen enabledness.
for event in (commit,cancel):
    event['params'].append('R')
    event['guards'].append('R = pending ∖ {j}')
    start=len(event['guards'])
    event['guards']+=['pending = R ∪ {j}','j ∉ R','finite(R)']
    event['theorem_guards']=list(range(start,len(event['guards'])))
    event['actions'][0]='pending ≔ R'
m0=dict(name='M0_AuthorityLedger',ref=None,variables=variables0,invariants=invariants0,events=[ev('INITIALISATION',actions=init0),ev('SetAuthority',['P'],['P ⊆ NODE × CAP'],['auth ≔ P']),reserve,commit,cancel])
variables1=variables0+['issued','scope','revoked']
invariants1=[('inv11','issued ⊆ NODE'),('inv12','root ∈ issued'),('inv13','scope ⊆ NODE × CAP'),('inv13d','dom(scope) = issued'),('inv13b','∀a · a ∈ NODE ∖ issued ⇒ scope[{a}] = ∅'),('inv14','scope[{root}] = rootScope'),('inv15','revoked ⊆ issued'),('inv16','∀a · a ∈ issued ⇒ path(a) ⊆ issued'),('inv16b','∀a · a ∈ issued ∖ {root} ⇒ parent(a) ∈ issued'),('inv17','∀a · a ∈ issued ∖ {root} ⇒ scope[{a}] ⊆ scope[{parent(a)}]'),('inv18','∀a · a ∈ issued ⇒ scope[{a}] ≠ ∅'),('inv18b','∀a · a ∈ issued ⇒ scope[{a}] ⊆ rootScope'),('inv19','auth = '+auth())]
delegate=ev('Delegate',['a','S','P'],['a ∈ NODE ∖ issued','a ∈ NODE ∖ {root}','parent(a) ∈ issued','path(parent(a)) ∩ revoked = ∅','S ⊆ scope[{parent(a)}]','S ⊆ CAP','S ≠ ∅','P = '+auth('(issued ∪ {a})','(scope ∪ ({a} × S))')],['auth ≔ P','issued ≔ issued ∪ {a}','scope ≔ scope ∪ ({a} × S)'],ref='SetAuthority')
revoke=ev('Revoke',['a','P'],['a ∈ issued ∖ revoked','P = '+auth(revoked='(revoked ∪ {a})')],['auth ≔ P','revoked ≔ revoked ∪ {a}'],ref='SetAuthority')
def refining(e):
    r=deepcopy(e);r['ref']=e['name'];return r
m1=dict(name='M1_DelegationChain',ref=m0['name'],variables=variables1,invariants=invariants1,events=[ev('INITIALISATION',actions=init0+['issued ≔ {root}','scope ≔ {root} × rootScope','revoked ≔ ∅']),delegate,revoke,refining(reserve),refining(commit),refining(cancel)])
m2events=[refining(e) for e in m1['events']]
for e in m2events:
    if e['name']=='INITIALISATION':
        e['ref']=None;e['actions']+=['submitted ≔ ∅','effectCount ≔ JOB × {0}','badUse ≔ FALSE']
    elif e['name']=='Reserve':e['actions']+=['badUse ≔ bool(badUse = TRUE ∨ owner(j) ↦ need(j) ∉ auth)']
    elif e['name']=='Commit':
        e['guards']+=['j ∈ submitted']
        e['actions']+=['submitted ≔ submitted ∖ {j}','effectCount(j) ≔ effectCount(j) + 1','badUse ≔ bool(badUse = TRUE ∨ owner(j) ↦ need(j) ∉ auth)']
    elif e['name']=='CancelConfirmed':e['actions']+=['submitted ≔ submitted ∖ {j}']
m2events.insert(4,ev('Submit',['j'],['j ∈ pending ∖ submitted','owner(j) ↦ need(j) ∈ auth'],['submitted ≔ submitted ∪ {j}','badUse ≔ bool(badUse = TRUE ∨ owner(j) ↦ need(j) ∉ auth)'],convergent=True))
# Name the remaining unsubmitted jobs, exposing the singleton removed by
# Submit. Every additional algebraic fact is a proved theorem guard.
submit=next(e for e in m2events if e['name']=='Submit')
submit['params'].append('T')
submit['guards'].append('T = (pending ∖ submitted) ∖ {j}')
start=len(submit['guards'])
submit['guards']+=['pending ∖ submitted = T ∪ {j}','j ∉ T','pending ∖ (submitted ∪ {j}) = T','finite(T)','card(pending ∖ submitted) = card(T) + 1','card(pending ∖ (submitted ∪ {j})) = card(T)']
submit['theorem_guards']=list(range(start,len(submit['guards'])))
m2=dict(name='M2_SubmittedObligations',ref=m1['name'],variables=variables1+['submitted','effectCount','badUse'],variant='card(pending ∖ submitted)',invariants=[('inv20','submitted ⊆ pending'),('inv21','effectCount ∈ JOB → ℕ'),('inv22a','∀j · j ∈ committed ⇒ effectCount(j) = 1'),('inv22b','∀j · j ∈ JOB ∖ committed ⇒ effectCount(j) = 0'),('inv23','∀j · j ∈ JOB ⇒ effectCount(j) ≤ 1'),('inv24','badUse ∈ BOOL'),('inv25','badUse = FALSE')],events=m2events)
m3=deepcopy(m2)
m3.update(name='M3_Pilot',ref=m2['name'],invariants=[])
m3.pop('variant',None)
m3['events']=[refining(e) if e['name']!='INITIALISATION' else deepcopy(e) for e in m2['events']]
models=[m0,m1,m2,m3]
pilot_constants=['u','a1','a2','a3','readCap','writeCap','req1','req2','req3']
pilot_axioms=[('pilot01','partition(NODE, {u}, {a1}, {a2}, {a3})'),('pilot02','partition(CAP, {readCap}, {writeCap})'),('pilot03','partition(JOB, {req1}, {req2}, {req3})'),('pilot04','root = u'),('pilot05','rootScope = CAP'),('pilot06','parent = {a1 ↦ u, a2 ↦ a1, a3 ↦ a1}'),('pilot07','rank = {u ↦ 0, a1 ↦ 1, a2 ↦ 2, a3 ↦ 2}'),('pilot08','path = {u ↦ {u}, a1 ↦ {u,a1}, a2 ↦ {u,a1,a2}, a3 ↦ {u,a1,a3}}'),('pilot09','owner = {req1 ↦ a1, req2 ↦ a2, req3 ↦ a3}'),('pilot10','need = {req1 ↦ readCap, req2 ↦ writeCap, req3 ↦ readCap}'),('pilot11','budget = 2')]

def build():
    OUT.mkdir(exist_ok=True)
    context=ET.Element(P+'contextFile',{P+'configuration':P+'fwd','version':'3'})
    for i,s in enumerate(sets):element(context,'carrierSet',f's{i}',identifier=s)
    for i,c in enumerate(constants):element(context,'constant',f'c{i}',identifier=c)
    for label,pred in axioms:element(context,'axiom',label,label=label,predicate=pred,theorem='false')
    write(context,OUT/'C_Delegation.buc')
    pilot=ET.Element(P+'contextFile',{P+'configuration':P+'fwd','version':'3'})
    element(pilot,'extendsContext','extends',target='C_Delegation')
    for i,c in enumerate(pilot_constants):element(pilot,'constant',f'c{i}',identifier=c)
    for label,pred in pilot_axioms:element(pilot,'axiom',label,label=label,predicate=pred,theorem='false')
    write(pilot,OUT/'C_Pilot.buc')
    for m in models:
        r=ET.Element(P+'machineFile',{P+'configuration':P+'fwd','version':'5'})
        if m['ref']:element(r,'refinesMachine','ref',target=m['ref'])
        element(r,'seesContext','see',target='C_Pilot' if m['name']=='M3_Pilot' else 'C_Delegation')
        for i,v in enumerate(m['variables']):element(r,'variable',f'v{i}',identifier=v)
        for label,pred in m['invariants']:element(r,'invariant',label,label=label,predicate=pred,theorem='false')
        if 'variant' in m:element(r,'variant','variant',expression=m['variant'])
        for i,e in enumerate(m['events']):
            x=element(r,'event',f'e{i}',label=e['name'],convergence='1' if e['convergent'] else '0',extended='false')
            if e['ref']:element(x,'refinesEvent','ref',target=e['ref'])
            for k,v in enumerate(e['params']):element(x,'parameter',f'p{k}',identifier=v)
            for k,g in enumerate(e['guards']):element(x,'guard',f'g{k}',label=f'grd{k+1}',predicate=g,theorem='true' if k in e.get('theorem_guards',[]) else 'false')
            for k,a in enumerate(e['actions']):element(x,'action',f'a{k}',label=f'act{k+1}',assignment=a)
        write(r,OUT/(m['name']+'.bum'))
    project=ET.Element('projectDescription');ET.SubElement(project,'name').text='DelegatedAuthorization';ET.SubElement(project,'comment').text='Delegated authorization with effective revocation and obligation accounting'
    ET.SubElement(project,'projects');bs=ET.SubElement(project,'buildSpec');cmd=ET.SubElement(bs,'buildCommand');ET.SubElement(cmd,'name').text='org.rodinp.core.rodinbuilder';ET.SubElement(cmd,'arguments');ET.SubElement(ET.SubElement(project,'natures'),'nature').text='org.rodinp.core.rodinnature'
    write(project,OUT/'.project')
    spec=dict(sets=sets,constants=constants,axioms=axioms,pilot_constants=pilot_constants,pilot_axioms=pilot_axioms,models=models)
    (BASE/'model_spec.json').write_text(json.dumps(spec,ensure_ascii=False,indent=2)+'\n')
    text=['CONTEXT C_Delegation','SETS '+', '.join(sets),'CONSTANTS '+', '.join(constants),'AXIOMS']+[f'  @{l} {p}' for l,p in axioms]+['END','']
    text+=['CONTEXT C_Pilot','EXTENDS C_Delegation','CONSTANTS '+', '.join(pilot_constants),'AXIOMS']+[f'  @{l} {p}' for l,p in pilot_axioms]+['END','']
    for m in models:
        text+=['MACHINE '+m['name']]+(['REFINES '+m['ref']] if m['ref'] else [])+['SEES '+('C_Pilot' if m['name']=='M3_Pilot' else 'C_Delegation'),'VARIABLES '+', '.join(m['variables']),'INVARIANTS']+[f'  @{l} {p}' for l,p in m['invariants']]
        if 'variant' in m:text+=['VARIANT '+m['variant']]
        text+=['EVENTS']
        for e in m['events']:
            text+=['  EVENT '+e['name']+(' CONVERGENT' if e['convergent'] else '')]
            if e['ref']:text+=['    REFINES '+e['ref']]
            if e['params']:text+=['    ANY '+', '.join(e['params'])]
            if e['guards']:text+=['    WHERE']+[f'      @grd{i+1} '+('[theorem] ' if i in e.get('theorem_guards',[]) else '')+g for i,g in enumerate(e['guards'])]
            text+=['    THEN']+[f'      @act{i+1} {a}' for i,a in enumerate(e['actions'])]+['    END']
        text+=['END','']
    (BASE/'docs/MODELS.eventb.txt').write_text('\n'.join(text))
    print('Generated 2 contexts, 4 machines, Eclipse project, JSON specification and readable listing.')
if __name__=='__main__':build()
