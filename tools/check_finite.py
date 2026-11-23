#!/usr/bin/env python3
"""Independent finite interpretation of the specified transitions.
Checks invariants, event simulation M2->M1->M0 and Submit convergence.
This is not a Rodin parser, POG or proof engine.
"""
from dataclasses import dataclass, replace
from collections import deque
from pathlib import Path
import json,time,platform
BASE=Path(__file__).resolve().parents[1]
@dataclass(frozen=True)
class State:
    scope: tuple
    revoked: frozenset
    pending: frozenset
    committed: frozenset
    cancelled: frozenset
    used: int
    submitted: frozenset
    count: tuple
    bad: bool=False

def run(n,m,budget,shape):
    parent=[None]+[a-1 if shape=='chain' else 0 for a in range(1,n)]
    paths=[]
    for a in range(n):paths.append(frozenset({a}) if a==0 else paths[parent[a]]|{a})
    owners=[1+j%(n-1) for j in range(m)];needs=[1 if j%2==0 else 2 for j in range(m)]
    def authority(s):
        return frozenset((a,k) for a in range(n) for k in (1,2) if s.scope[a]&k and not(paths[a]&s.revoked))
    def invariants(s):
        issued={a for a in range(n) if s.scope[a]}
        assert 0 in issued and s.scope[0]==3
        assert s.revoked<=issued
        relation={(a,k) for a in range(n) for k in (1,2) if s.scope[a]&k}
        assert {a for a,k in relation}==issued
        assert relation & {(a,k) for a in range(n) for k in (1,2) if not paths[a]&s.revoked}==set(authority(s))
        assert all(paths[a]<=issued for a in issued)
        assert all(s.scope[a]&s.scope[parent[a]]==s.scope[a] for a in issued-{0})
        assert not(s.pending&s.committed or s.pending&s.cancelled or s.committed&s.cancelled)
        assert s.used==len(s.pending)+len(s.committed)<=budget
        assert s.submitted<=s.pending
        assert all(s.count[j]==int(j in s.committed) for j in range(m))
        assert all(c<=1 for c in s.count) and not s.bad
        # Independently compute live authorization by walking parents.
        def live(a):
            while a is not None:
                if not s.scope[a] or a in s.revoked:return False
                a=parent[a]
            return True
        assert authority(s)==frozenset((a,k) for a in range(n) for k in (1,2) if live(a) and s.scope[a]&k)
    def step(s):
        for a in range(1,n):
            p=parent[a]
            if s.scope[a]==0 and s.scope[p] and not paths[p]&s.revoked:
                for mask in (1,2,3):
                    if mask&s.scope[p]==mask:
                        v=s.scope[:a]+(mask,)+s.scope[a+1:]
                        yield ('Delegate',a,mask),replace(s,scope=v)
        for a in range(n):
            if s.scope[a] and a not in s.revoked:yield ('Revoke',a),replace(s,revoked=s.revoked|{a})
        auth=authority(s)
        for j in range(m):
            permitted=(owners[j],needs[j]) in auth
            if j not in s.pending|s.committed|s.cancelled and permitted and s.used<budget:
                yield ('Reserve',j),replace(s,pending=s.pending|{j},used=s.used+1,bad=s.bad or not permitted)
            if j in s.pending-s.submitted and permitted:
                yield ('Submit',j),replace(s,submitted=s.submitted|{j},bad=s.bad or not permitted)
            if j in s.submitted and permitted:
                v=s.count[:j]+(s.count[j]+1,)+s.count[j+1:]
                yield ('Commit',j),replace(s,pending=s.pending-{j},submitted=s.submitted-{j},committed=s.committed|{j},count=v,bad=s.bad or not permitted)
            if j in s.pending:
                yield ('CancelConfirmed',j),replace(s,pending=s.pending-{j},submitted=s.submitted-{j},cancelled=s.cancelled|{j},used=s.used-1)
    def simulate(s,e,t):
        a=authority(s);ap=authority(t);kind=e[0]
        ledger=lambda u:(u.pending,u.committed,u.cancelled,u.used)
        concrete1=lambda u:(u.scope,u.revoked,ledger(u),authority(u))
        if kind in ('Commit','CancelConfirmed'):
            j=e[1];rest=s.pending-{j}
            assert s.pending==rest|{j} and j not in rest
            assert len(s.pending)==len(rest)+1
        if kind=='Submit':
            j=e[1];rest=(s.pending-s.submitted)-{j}
            assert s.pending-s.submitted==rest|{j} and j not in rest
            assert s.pending-(s.submitted|{j})==rest
            assert len(s.pending-s.submitted)==len(rest)+1
        if kind in ('Delegate','Revoke'):
            # M1 events refine M0.SetAuthority(P=ap).
            assert ledger(s)==ledger(t)
            assert ap<=frozenset((x,k) for x in range(n) for k in (1,2))
        elif kind=='Submit':
            # New convergent event refines skip in M1 (and M0).
            assert concrete1(s)==concrete1(t)
            assert len(t.pending-t.submitted)<len(s.pending-s.submitted)
        else:
            j=e[1];assert a==ap
            assert s.scope==t.scope and s.revoked==t.revoked
            if kind=='Reserve':
                assert (owners[j],needs[j]) in a and s.used<budget
                assert j not in s.pending|s.committed|s.cancelled
                assert ledger(t)==(s.pending|{j},s.committed,s.cancelled,s.used+1)
            elif kind=='Commit':
                assert j in s.pending and (owners[j],needs[j]) in a
                assert ledger(t)==(s.pending-{j},s.committed|{j},s.cancelled,s.used)
            elif kind=='CancelConfirmed':
                assert j in s.pending
                assert ledger(t)==(s.pending-{j},s.committed,s.cancelled|{j},s.used-1)
    start=time.perf_counter()
    s0=State((3,)+(0,)*(n-1),frozenset(),frozenset(),frozenset(),frozenset(),0,frozenset(),(0,)*m)
    seen={s0};q=deque([s0]);edges=0;event_counts={};examples={}
    while q:
        s=q.popleft();invariants(s)
        for e,t in step(s):
            edges+=1;invariants(t);simulate(s,e,t)
            event_counts[e[0]]=event_counts.get(e[0],0)+1
            if e[0]=='Submit':examples.setdefault('Submit decreases variant',True)
            if t not in seen:seen.add(t);q.append(t)
    assert set(event_counts)=={'Delegate','Revoke','Reserve','Submit','Commit','CancelConfirmed'}
    return dict(nodes=n,jobs=m,budget=budget,shape=shape,states=len(seen),transitions=edges,event_counts=event_counts,seconds=time.perf_counter()-start,status='EXHAUSTED_SAFE_SIMULATION_CHECKED')
if __name__=='__main__':
    runs=[]
    for args in [(3,2,1,'chain'),(3,2,2,'chain'),(3,2,1,'star'),(4,3,2,'chain'),(4,3,2,'star'),(5,3,2,'chain')]:
        r=run(*args);runs.append(r);print(json.dumps(r),flush=True)
    report=dict(method='Independent Python finite interpretation; not native Rodin validation',python=platform.python_version(),runs=runs)
    (BASE/'validation/finite_validation.json').write_text(json.dumps(report,indent=2)+'\n')
