#!/usr/bin/env python3
"""Run local tools, bounded differential conformance, mutants and controlled races."""
from pathlib import Path
from collections import deque
from concurrent.futures import ThreadPoolExecutor
import csv,json,platform,sqlite3,threading,time
from monitor import Config,Monitor,ToolAgent
from oracle import Oracle

BASE=Path(__file__).resolve().parent;OUT=BASE/'results'
PILOT=Config((None,0,1,1),(1,2,3),(1,2,1),2)
ISSUE=[('Delegate',1,3),('Delegate',2,2),('Delegate',3,1)]
SCENARIOS={
 'happy_path':ISSUE+[('Reserve',2),('Submit',2),('Commit',2),('Reserve',1),('Submit',1),('Commit',1)],
 'scope_expansion':[('Delegate',1,1),('Delegate',2,2)],
 'local_revocation':ISSUE[:2]+[('Revoke',1),('Reserve',1)],
 'cached_authorization':ISSUE[:2]+[('Reserve',1),('Submit',1),('Revoke',1),('Commit',1)],
 'no_shared_budget':ISSUE+[('Reserve',1),('Reserve',2),('Reserve',0)],
 'early_release':ISSUE[:2]+[('Reserve',1),('Submit',1),('ReleaseUnconfirmed',1)],
 'replay_commit':ISSUE[:2]+[('Reserve',1),('Submit',1),('Commit',1),('Commit',1)],
}
MUTANTS=list(SCENARIOS)[1:]

def scenario(name,mutant='correct',save_database=False):
    oracle=Oracle(PILOT);s=oracle.initial
    database=OUT/'case_study.sqlite' if save_database else ':memory:'
    if save_database and database.exists():database.unlink()
    sut=Monitor(PILOT,mutant,str(database));trace=[];divergences=[];violations=set()
    actors={a:ToolAgent(a,sut) for a in (1,2,3)}
    for i,command in enumerate(SCENARIOS[name]):
        before=sut.snapshot();expected,t=oracle.step(s,command)
        if command[0] in ('Reserve','Submit','Commit','CancelConfirmed'):
            accepted,reason=actors[PILOT.owners[command[1]]].request(command[0],command[1])
        else:accepted,reason=sut.apply(command)
        actual=sut.snapshot();errors=oracle.requirements(actual,before,command,accepted)
        conforms=accepted==expected and actual==oracle.wire(t)
        if not conforms:divergences.append(i)
        violations.update(errors)
        trace.append(dict(step=i,command=command,expected_accept=expected,actual_accept=accepted,reason=reason,conforms=conforms,requirements_violated=errors,actual=actual,expected=oracle.wire(t)))
        s=t
    tools=[dict(id=r[0],job=r[1],tool=r[2],result=json.loads(r[3])) for r in sut.db.execute('SELECT id,job,tool,result FROM tool_effects ORDER BY id')]
    releases=list(sut.db.execute('SELECT job,version FROM release_registry ORDER BY id'))
    sut.close()
    return dict(scenario=name,variant=mutant,steps=len(trace),first_divergence=divergences[0] if divergences else None,conformant=not divergences,violations=sorted(violations),trace=trace,tool_effects=tools,release_registry=releases)

def bounded(config,label):
    oracle=Oracle(config);commands=list(oracle.commands());seen={oracle.initial:()};queue=deque([oracle.initial]);checked=enabled=rejected=0
    start=time.perf_counter()
    while queue:
        s=queue.popleft();prefix=seen[s];sut=Monitor(config)
        for command in prefix:assert sut.apply(command)[0]
        before=sut.snapshot();assert before==oracle.wire(s)
        for command in commands:
            # Each outgoing transition is tried against a real implementation state
            # reached by replay, then rolled back independently of the monitor's savepoint.
            sut.db.execute('SAVEPOINT trial')
            expected,t=oracle.step(s,command);actual,_=sut.apply(command);after=sut.snapshot()
            assert actual==expected,(label,prefix,command,'enabledness mismatch')
            assert after==oracle.wire(t),(label,prefix,command,'state mismatch',after,oracle.wire(t))
            assert not oracle.requirements(after,before,command,actual),(label,prefix,command,'requirement violation')
            checked+=1;enabled+=int(actual);rejected+=int(not actual)
            if expected and t not in seen:seen[t]=prefix+(command,);queue.append(t)
            sut.db.execute('ROLLBACK TO trial');sut.db.execute('RELEASE trial')
        assert sut.snapshot()==before
        sut.close()
    return dict(configuration=label,nodes=len(config.parents),jobs=len(config.owners),budget=config.budget,states=len(seen),checked_commands=checked,enabled_edges=enabled,rejected_inputs=rejected,seconds=time.perf_counter()-start,status='EXHAUSTED_CONFORMANT')

def concurrency(trials=100):
    result=[]
    for unsafe in (False,True):
        accepted_counts=[];failures=0;start=time.perf_counter()
        for _ in range(trials):
            sut=Monitor(Config(PILOT.parents,PILOT.owners,PILOT.needs,1))
            for c in ISSUE:assert sut.apply(c)[0]
            barrier=threading.Barrier(2)
            def worker(j):
                if unsafe:return sut.unsafe_reserve_at_barrier(j,barrier)[0]
                barrier.wait(timeout=10);return sut.apply(('Reserve',j))[0]
            with ThreadPoolExecutor(max_workers=2) as pool:
                futures=[pool.submit(worker,j) for j in (1,2)]
                count=sum(f.result(timeout=15) for f in futures)
            snapshot=sut.snapshot();violations=Oracle(sut.config).requirements(snapshot)
            failures+=int(bool(violations));accepted_counts.append(count);sut.close()
        expected=2 if unsafe else 1
        assert accepted_counts==[expected]*trials
        assert failures==(trials if unsafe else 0)
        result.append(dict(variant='non_atomic_reserve' if unsafe else 'atomic_monitor',trials=trials,accepted_per_trial=expected,requirement_violations=failures,schedule='Both unsafe reads complete before either write; safe calls start at a shared barrier.',seconds=time.perf_counter()-start))
    return result

def revocation_orders(trials=50):
    result=[]
    for revoke_first in (True,False):
        effects=[];accepted=[]
        for _ in range(trials):
            sut=Monitor(PILOT)
            for c in ISSUE[:2]+[('Reserve',1),('Submit',1)]:assert sut.apply(c)[0]
            ready=threading.Event()
            def first():
                out=sut.apply(('Revoke',1) if revoke_first else ('Commit',1));ready.set();return out
            def second():
                assert ready.wait(timeout=10)
                return sut.apply(('Commit',1) if revoke_first else ('Revoke',1))
            with ThreadPoolExecutor(max_workers=2) as pool:
                f1=pool.submit(first);f2=pool.submit(second);a=f1.result(timeout=15);b=f2.result(timeout=15)
            snapshot=sut.snapshot();assert not Oracle(PILOT).requirements(snapshot)
            commit_ok=b[0] if revoke_first else a[0]
            assert commit_ok is (not revoke_first)
            accepted.append(commit_ok);effects.append(snapshot['effects'][1]);sut.close()
        result.append(dict(order='Revoke_then_Commit' if revoke_first else 'Commit_then_Revoke',trials=trials,commits_accepted=sum(accepted),tool_effects=sum(effects),status='EXPECTED_LINEARIZATION'))
    return result

def rollback_check():
    sut=Monitor(PILOT)
    for c in ISSUE[:2]+[('Reserve',1),('Submit',1)]:assert sut.apply(c)[0]
    before=sut.snapshot()
    sut.db.execute("CREATE TRIGGER injected_tool_failure BEFORE INSERT ON tool_effects BEGIN SELECT RAISE(ABORT,'injected local tool failure'); END")
    failed=False
    try:sut.apply(('Commit',1))
    except sqlite3.IntegrityError:failed=True
    assert failed and sut.snapshot()==before
    assert sut.db.execute('SELECT count(*) FROM release_registry').fetchone()[0]==0
    sut.db.execute('DROP TRIGGER injected_tool_failure')
    assert sut.apply(('Commit',1))[0]
    after=sut.snapshot();assert after['effects'][1]==1 and not Oracle(PILOT).requirements(after)
    sut.close()
    return dict(status='ROLLBACK_AND_RETRY_PASSED',failed_commit_state_unchanged=True,partial_release_rows_after_failure=0,effects_after_retry=1,scope='Local SQLite tool effect and monitor state share one transaction; not an external-service crash test.')

def adapter_check():
    sut=Monitor(PILOT);agent=ToolAgent(3,sut);before=sut.snapshot();denied=0
    for operation,job in [('Reserve',1),('Revoke',2)]:
        try:agent.request(operation,job)
        except ValueError:denied+=1
    assert denied==2 and sut.snapshot()==before;sut.close()
    return dict(cross_owner_request_rejected=True,administrative_operation_not_exposed=True,scope='Adapter checks only; Python-process isolation is assumed, not provided.')

def main():
    OUT.mkdir(exist_ok=True);start=time.perf_counter()
    scenarios=[scenario(name,save_database=name=='happy_path') for name in SCENARIOS]
    assert all(r['conformant'] and not r['violations'] for r in scenarios)
    assert len(scenarios[0]['tool_effects'])==2 and len(scenarios[0]['release_registry'])==1
    mutants=[scenario(name,name) for name in MUTANTS]
    assert all(not r['conformant'] and r['violations'] for r in mutants)
    results=[]
    for shape in ('chain','star'):
        for budget in (1,2):
            c=Config((None,0,1) if shape=='chain' else (None,0,0),(1,2),(1,2),budget)
            r=bounded(c,f'{shape}_budget{budget}');results.append(r);print(json.dumps(r),flush=True)
    races=concurrency();orders=revocation_orders();rollback=rollback_check();adapter=adapter_check()
    report=dict(environment=dict(python=platform.python_version(),sqlite=sqlite3.sqlite_version,platform=platform.platform()),case_study='Scripted release-preparation agents and executable local SQLite tool adapters; no LLM, external service or deployed product.',correct_scenarios=scenarios,implementation_mutants=mutants,bounded_conformance=results,concurrency=races,revocation_linearizations=orders,local_tool_rollback=rollback,adapter_checks=adapter,seconds=time.perf_counter()-start)
    (OUT/'implementation_results.json').write_text(json.dumps(report,indent=2)+'\n')
    with (OUT/'implementation_mutants.csv').open('w') as f:
        w=csv.DictWriter(f,fieldnames=['mutant','detected','first_divergence','requirements']);w.writeheader()
        for r in mutants:w.writerow(dict(mutant=r['variant'],detected=not r['conformant'],first_divergence=r['first_divergence'],requirements=';'.join(r['violations'])))
    print(json.dumps(dict(correct_scenarios=len(scenarios),mutants_detected=len(mutants),bounded_states=sum(r['states'] for r in results),checked_commands=sum(r['checked_commands'] for r in results),concurrency=races,revocation_orders=orders,total_seconds=report['seconds']),indent=2),flush=True)
if __name__=='__main__':main()
