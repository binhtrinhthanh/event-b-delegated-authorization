"""Independent executable interpretation of M2; NOT the native Rodin engine.
Pure immutable state; no SQLite and no import of monitor.py.
"""
from dataclasses import dataclass,replace

@dataclass(frozen=True)
class State:
    scopes: tuple
    revoked: tuple
    phases: tuple
    effects: tuple
    used: int=0

def put(values,index,value):return values[:index]+(value,)+values[index+1:]

class Oracle:
    def __init__(self,config):
        self.c=config;self.paths=[]
        for a,parent in enumerate(config.parents):
            self.paths.append(frozenset({a}) if parent is None else self.paths[parent]|{a})
        self.initial=State((config.root_scope,)+(0,)*(len(config.parents)-1),(False,)*len(config.parents),(0,)*len(config.owners),(0,)*len(config.owners))

    def live(self,s,a):return all(s.scopes[p] and not s.revoked[p] for p in self.paths[a])
    def allowed(self,s,j):return self.live(s,self.c.owners[j]) and bool(s.scopes[self.c.owners[j]]&self.c.needs[j])
    def wire(self,s):
        return dict(scopes=list(s.scopes),revoked=list(s.revoked),phases=list(s.phases),
                    pending=[j for j,x in enumerate(s.phases) if x in (1,2)],used=s.used,effects=list(s.effects),
                    auth=[s.scopes[a] if self.live(s,a) else 0 for a in range(len(s.scopes))])

    def step(self,s,command):
        operation,*args=command;c=self.c
        if operation=='Delegate':
            a,mask=args
            if not(0<a<len(s.scopes) and s.scopes[a]==0 and 0<mask<4):return False,s
            p=c.parents[a]
            if not(self.live(s,p) and mask&s.scopes[p]==mask):return False,s
            return True,replace(s,scopes=put(s.scopes,a,mask))
        if operation=='Revoke':
            a=args[0]
            if not(0<=a<len(s.scopes) and s.scopes[a] and not s.revoked[a]):return False,s
            return True,replace(s,revoked=put(s.revoked,a,True))
        if operation not in ('Reserve','Submit','Commit','CancelConfirmed'):return False,s
        j=args[0]
        if not(0<=j<len(s.phases)):return False,s
        phase=s.phases[j]
        if operation=='Reserve':
            if phase!=0 or not self.allowed(s,j) or s.used>=c.budget:return False,s
            return True,replace(s,phases=put(s.phases,j,1),used=s.used+1)
        if operation=='Submit':
            if phase!=1 or not self.allowed(s,j):return False,s
            return True,replace(s,phases=put(s.phases,j,2))
        if operation=='Commit':
            if phase!=2 or not self.allowed(s,j):return False,s
            return True,replace(s,phases=put(s.phases,j,3),effects=put(s.effects,j,s.effects[j]+1))
        if phase not in (1,2):return False,s
        return True,replace(s,phases=put(s.phases,j,4),used=s.used-1)

    def commands(self,include_negative=True):
        for a in range(1,len(self.c.parents)):
            for mask in ((0,1,2,3) if include_negative else (1,2,3)):yield ('Delegate',a,mask)
        for a in range(len(self.c.parents)):yield ('Revoke',a)
        for op in ['Reserve','Submit','Commit','CancelConfirmed']+(['ReleaseUnconfirmed'] if include_negative else []):
            for j in range(len(self.c.owners)):yield (op,j)

    def requirements(self,w,before=None,command=None,accepted=False):
        """Fixed requirements for both correct implementation and mutants."""
        failures=[];c=self.c
        scopes=w['scopes'];revoked=w['revoked'];issued={a for a,v in enumerate(scopes) if v}
        if any(c.parents[a] not in issued or scopes[a]&scopes[c.parents[a]]!=scopes[a] for a in issued-{0}):failures.append('scope_attenuation')
        if any(scopes[a]&c.root_scope!=scopes[a] for a in issued):failures.append('root_scope_bound')
        pending=set(w['pending']);committed={j for j,p in enumerate(w['phases']) if p==3}
        if pending!={j for j,p in enumerate(w['phases']) if p in (1,2)}:failures.append('obligation_coverage')
        if w['used']!=len(pending)+len(committed):failures.append('ledger_conservation')
        if not(0<=w['used']<=c.budget):failures.append('shared_budget')
        if any(k>1 for k in w['effects']):failures.append('at_most_once')
        if any(k!=int(j in committed) for j,k in enumerate(w['effects'])):failures.append('effect_count_membership')
        expected_auth=[scopes[a] if all(scopes[p] and not revoked[p] for p in self.paths[a]) else 0 for a in range(len(scopes))]
        if w['auth']!=expected_auth:failures.append('live_chain_authority')
        if before is not None and accepted and command[0] in ('Reserve','Submit','Commit'):
            j=command[1];a=c.owners[j]
            live=all(before['scopes'][p] and not before['revoked'][p] for p in self.paths[a])
            if not(live and before['scopes'][a]&c.needs[j]):failures.append('authorization_at_use')
        return failures
