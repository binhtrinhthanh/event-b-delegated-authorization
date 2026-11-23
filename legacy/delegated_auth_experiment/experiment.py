"""Finite-state exhaustive exploration; NOT a Rodin/ProB proof.
No third-party dependencies. Run: python3 experiment.py
"""
from dataclasses import dataclass, replace, asdict
from collections import deque
from pathlib import Path
import json, csv, time, platform

@dataclass(frozen=True)
class State:
    scopes: tuple   # 0=not issued, 1=read, 2=write, 3=both
    revoked: int
    jobs: tuple     # 0=new, 1=reserved, 2=submitted, 3=paid, 4=cancelled
    held: tuple
    payments: tuple

def update(t, i, v):
    return t[:i]+(v,)+t[i+1:]

def run(n=3, jobs=2, budget=2, topology='chain', mutant='correct'):
    parents = tuple([-1]+[i-1 if topology=='chain' else 0 for i in range(1,n)])
    owners = tuple(1+j%(n-1) for j in range(jobs))
    initial = State((1,)+(0,)*(n-1),0,(0,)*jobs,(0,)*jobs,(0,)*jobs)
    def live(s,a,local=False):
        while a>=0:
            if not s.scopes[a] or s.revoked>>a&1: return False
            if local: break
            a=parents[a]
        return True
    def authorized(s,a):
        return live(s,a) and bool(s.scopes[a]&1)
    def successors(s):
        for a in range(1,n):
            p=parents[a]
            if not s.scopes[a] and live(s,p):
                for scope in (1,2,3):
                    if mutant=='scope_expansion' or scope&s.scopes[p]==scope:
                        yield f'Delegate({p}->{a},scope={scope})', replace(s,scopes=update(s.scopes,a,scope))
        for a in range(n):
            if s.scopes[a] and not (s.revoked>>a&1):
                yield f'Revoke({a})', replace(s,revoked=s.revoked|1<<a)
        for j,a in enumerate(owners):
            status=s.jobs[j]
            effective = live(s,a,local=mutant=='local_revocation') and bool(s.scopes[a]&1)
            available = sum(s.payments)+sum(s.held)<budget
            if status==0 and effective and (available or mutant=='no_shared_budget'):
                yield f'Reserve(job={j},agent={a})', replace(s,jobs=update(s.jobs,j,1),held=update(s.held,j,1))
            if status==1 and effective:
                yield f'Submit(job={j})',replace(s,jobs=update(s.jobs,j,2))
            if status==2 and (effective or mutant=='cached_authorization') and (s.held[j] or (mutant=='early_release' and available)):
                yield f'Commit(job={j},agent={a})',replace(s,jobs=update(s.jobs,j,3),held=update(s.held,j,0),payments=update(s.payments,j,s.payments[j]+1))
            if status in (1,2):
                yield f'CancelConfirmed(job={j})',replace(s,jobs=update(s.jobs,j,4),held=update(s.held,j,0))
            if mutant=='early_release' and status==2 and s.held[j]:
                yield f'ReleaseBeforeCancel(job={j})',replace(s,held=update(s.held,j,0))
            if mutant=='replay_commit' and status==3 and s.payments[j]<2:
                yield f'ReplayCommit(job={j})',replace(s,payments=update(s.payments,j,s.payments[j]+1))
    def violations(before,event,s):
        errors=[]
        if any(s.scopes[a]&s.scopes[parents[a]]!=s.scopes[a] for a in range(1,n)):
            errors.append('scope_attenuation')
        if sum(s.payments)+sum(s.held)>budget: errors.append('shared_budget')
        if any(x>1 for x in s.payments): errors.append('at_most_once')
        if any(s.jobs[j] in (1,2) and s.held[j]!=1 for j in range(jobs)):
            errors.append('outstanding_obligation_covered')
        if event.startswith(('Reserve(', 'Submit(', 'Commit(')):
            j=int(event.split('job=')[1].split(',')[0].split(')')[0])
            if not authorized(before,owners[j]): errors.append('live_chain_at_use')
        return errors
    start=time.perf_counter(); queue=deque([initial]); pred={initial:None}; edges=0; maxdepth=0
    depth={initial:0}
    while queue:
        s=queue.popleft()
        for event,t in successors(s):
            edges+=1
            bad=violations(s,event,t)
            if bad:
                trace=[{'event':event,'state':asdict(t)}]; cursor=s
                while pred[cursor] is not None:
                    previous,label=pred[cursor]
                    trace.append({'event':label,'state':asdict(cursor)}); cursor=previous
                trace.append({'event':'INITIALISATION','state':asdict(initial)})
                trace.reverse()
                return dict(n=n,jobs=jobs,budget=budget,topology=topology,variant=mutant,status='VIOLATION',states=len(pred),transitions=edges,max_depth=maxdepth,seconds=time.perf_counter()-start,violations=bad,trace=trace)
            if t not in pred:
                pred[t]=(s,event);depth[t]=depth[s]+1;maxdepth=max(maxdepth,depth[t]);queue.append(t)
    return dict(n=n,jobs=jobs,budget=budget,topology=topology,variant=mutant,status='EXHAUSTED_SAFE',states=len(pred),transitions=edges,max_depth=maxdepth,seconds=time.perf_counter()-start,violations=[],trace=[])

def main():
    out=Path(__file__).parent/'results';out.mkdir(exist_ok=True)
    mutations=['scope_expansion','local_revocation','cached_authorization','no_shared_budget','early_release','replay_commit']
    results=[]
    for n,j,b in [(3,2,1),(3,2,2),(4,3,2),(4,3,3),(5,3,2),(6,4,2)]:
        for topology in ('chain','star'):
            results.append(run(n,j,b,topology))
    for mutation in mutations:
        results.append(run(3,2,1,'chain',mutation))
    assert all(r['status']=='EXHAUSTED_SAFE' for r in results[:12])
    assert all(r['status']=='VIOLATION' for r in results[12:])
    (out/'results.json').write_text(json.dumps({'environment':{'python':platform.python_version(),'platform':platform.platform()},'runs':results},indent=2))
    fields=['n','jobs','budget','topology','variant','status','states','transitions','max_depth','seconds','violations']
    with (out/'summary.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=fields);w.writeheader()
        for r in results:w.writerow({k:r[k] for k in fields})
    for r in results:
        print(r['n'],r['jobs'],r['budget'],r['topology'],r['variant'],r['status'],r['states'],r['transitions'],round(r['seconds'],4),r['violations'])
if __name__=='__main__':main()
