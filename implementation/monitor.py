"""Executable local tool gateway backed by SQLite.
Every safe operation, including the local tool effect, is one SQL transaction.
This is a prototype reference monitor, not an OAuth/MCP implementation.
"""
import json, sqlite3, threading
from dataclasses import dataclass

CAPS={1:'reports:read',2:'releases:publish'}
PHASES={'new':0,'reserved':1,'submitted':2,'committed':3,'cancelled':4}

@dataclass(frozen=True)
class Config:
    parents: tuple
    owners: tuple
    needs: tuple
    budget: int
    root_scope: int=3

class Rejected(Exception):pass

class Monitor:
    def __init__(self, config, mutant='correct', database=':memory:', initialize=True):
        self.config=config; self.mutant=mutant
        self.db=sqlite3.connect(database,isolation_level=None,check_same_thread=False,timeout=15)
        self.lock=threading.RLock()
        self.db.execute('PRAGMA foreign_keys=ON')
        self.db.execute('PRAGMA busy_timeout=15000')
        if initialize:self._initialize()

    def _initialize(self):
        c=self.db
        c.executescript('''
        CREATE TABLE principals(id INTEGER PRIMARY KEY,parent INTEGER,issued INTEGER NOT NULL,revoked INTEGER NOT NULL);
        CREATE TABLE grants(principal INTEGER NOT NULL,capability TEXT NOT NULL,PRIMARY KEY(principal,capability));
        CREATE TABLE jobs(id INTEGER PRIMARY KEY,owner INTEGER NOT NULL,need TEXT NOT NULL,phase TEXT NOT NULL);
        CREATE TABLE obligations(job INTEGER PRIMARY KEY REFERENCES jobs(id));
        CREATE TABLE quota(id INTEGER PRIMARY KEY CHECK(id=1),used INTEGER NOT NULL,capacity INTEGER NOT NULL);
        CREATE TABLE tool_effects(id INTEGER PRIMARY KEY AUTOINCREMENT,job INTEGER NOT NULL REFERENCES jobs(id),tool TEXT NOT NULL,result TEXT NOT NULL);
        CREATE TABLE release_registry(id INTEGER PRIMARY KEY AUTOINCREMENT,job INTEGER NOT NULL,version TEXT NOT NULL);
        CREATE TABLE audit(id INTEGER PRIMARY KEY AUTOINCREMENT,operation TEXT NOT NULL,arguments TEXT NOT NULL);
        CREATE TABLE reports(id INTEGER PRIMARY KEY,body TEXT NOT NULL);
        INSERT INTO reports VALUES(1,'Local release assessment: tests passed; deployment requires delegated publish permission.');
        ''')
        c.executemany('INSERT INTO principals VALUES(?,?,?,0)',[(i,p,int(i==0)) for i,p in enumerate(self.config.parents)])
        c.executemany('INSERT INTO grants VALUES(0,?)',[(name,) for bit,name in CAPS.items() if self.config.root_scope&bit])
        c.executemany('INSERT INTO jobs VALUES(?,?,?,?)',[(i,a,CAPS[k],'new') for i,(a,k) in enumerate(zip(self.config.owners,self.config.needs))])
        c.execute('INSERT INTO quota VALUES(1,0,?)',(self.config.budget,))

    def close(self):self.db.close()

    def _live(self, actor):
        # The implementation follows parent links using a recursive SQL query;
        # the independent oracle uses precomputed mathematical ancestor sets.
        if self.mutant=='local_revocation':
            row=self.db.execute('SELECT issued,revoked FROM principals WHERE id=?',(actor,)).fetchone()
            return row is not None and row==(1,0)
        rows=self.db.execute('''WITH RECURSIVE lineage(id,parent,issued,revoked) AS (
          SELECT id,parent,issued,revoked FROM principals WHERE id=?
          UNION ALL SELECT p.id,p.parent,p.issued,p.revoked FROM principals p JOIN lineage l ON p.id=l.parent
        ) SELECT issued,revoked FROM lineage''',(actor,)).fetchall()
        return bool(rows) and all(issued and not revoked for issued,revoked in rows)

    def _can(self, actor, capability):
        return self._live(actor) and self.db.execute('SELECT 1 FROM grants WHERE principal=? AND capability=?',(actor,capability)).fetchone() is not None

    def _job(self, j):
        row=self.db.execute('SELECT owner,need,phase FROM jobs WHERE id=?',(j,)).fetchone()
        if row is None:raise Rejected('unknown job')
        return row

    def _guard(self, predicate, reason):
        if not predicate:raise Rejected(reason)

    def _tool(self,j,cap):
        if cap=='reports:read':
            payload={'report':self.db.execute('SELECT body FROM reports WHERE id=1').fetchone()[0]}
        else:
            # A real local database effect, not an external irreversible release.
            self.db.execute('INSERT INTO release_registry(job,version) VALUES(?,?)',(j,f'candidate-{j}'))
            payload={'local_release':f'candidate-{j}'}
        self.db.execute('INSERT INTO tool_effects(job,tool,result) VALUES(?,?,?)',(j,cap,json.dumps(payload,sort_keys=True)))

    def apply(self, command):
        operation,*args=command
        with self.lock:
            self.db.execute('SAVEPOINT operation')
            try:
                if operation=='Delegate':
                    a,mask=args
                    row=self.db.execute('SELECT parent,issued FROM principals WHERE id=?',(a,)).fetchone()
                    self._guard(row is not None and not row[1] and row[0] is not None,'credential already issued or invalid')
                    parent=row[0]
                    self._guard(self._live(parent),'parent chain revoked or unissued')
                    self._guard(isinstance(mask,int) and 0<mask<4,'invalid scope')
                    rights={name for bit,name in CAPS.items() if mask&bit}
                    parent_rights={r[0] for r in self.db.execute('SELECT capability FROM grants WHERE principal=?',(parent,))}
                    if self.mutant!='scope_expansion':self._guard(rights<=parent_rights,'scope exceeds parent')
                    self.db.execute('UPDATE principals SET issued=1 WHERE id=?',(a,))
                    self.db.executemany('INSERT INTO grants VALUES(?,?)',[(a,k) for k in rights])
                elif operation=='Revoke':
                    a=args[0]
                    row=self.db.execute('SELECT issued,revoked FROM principals WHERE id=?',(a,)).fetchone()
                    self._guard(row==(1,0),'not a fresh issued revocation')
                    self.db.execute('UPDATE principals SET revoked=1 WHERE id=?',(a,))
                elif operation=='Reserve':
                    j=args[0];actor,cap,phase=self._job(j)
                    self._guard(phase=='new','job identifier already consumed')
                    self._guard(self._can(actor,cap),'no current capability')
                    used,budget=self.db.execute('SELECT used,capacity FROM quota').fetchone()
                    if self.mutant!='no_shared_budget':self._guard(used<budget,'capacity exhausted')
                    self.db.execute('INSERT INTO obligations VALUES(?)',(j,))
                    self.db.execute("UPDATE jobs SET phase='reserved' WHERE id=?",(j,))
                    self.db.execute('UPDATE quota SET used=used+1')
                elif operation=='Submit':
                    j=args[0];actor,cap,phase=self._job(j)
                    self._guard(phase=='reserved','job is not awaiting submit')
                    self._guard(self._can(actor,cap),'no current capability')
                    self.db.execute("UPDATE jobs SET phase='submitted' WHERE id=?",(j,))
                elif operation=='Commit':
                    j=args[0];actor,cap,phase=self._job(j)
                    replay=self.mutant=='replay_commit' and phase=='committed'
                    self._guard(phase=='submitted' or replay,'job not submitted or already consumed')
                    if self.mutant!='cached_authorization':self._guard(self._can(actor,cap),'capability no longer current')
                    if not replay:
                        self._guard(self.db.execute('SELECT 1 FROM obligations WHERE job=?',(j,)).fetchone() is not None,'no covered obligation')
                    self._tool(j,cap)
                    self.db.execute('DELETE FROM obligations WHERE job=?',(j,))
                    self.db.execute("UPDATE jobs SET phase='committed' WHERE id=?",(j,))
                    if replay:self.db.execute('UPDATE quota SET used=used+1')
                elif operation=='CancelConfirmed':
                    j=args[0];_,_,phase=self._job(j)
                    self._guard(phase in ('reserved','submitted'),'not a pending obligation')
                    self.db.execute('DELETE FROM obligations WHERE job=?',(j,))
                    self.db.execute("UPDATE jobs SET phase='cancelled' WHERE id=?",(j,))
                    self.db.execute('UPDATE quota SET used=used-1')
                elif operation=='ReleaseUnconfirmed':
                    self._guard(self.mutant=='early_release','unconfirmed cancellation cannot release resources')
                    j=args[0];_,_,phase=self._job(j)
                    self._guard(phase=='submitted','not a staged request')
                    self.db.execute('DELETE FROM obligations WHERE job=?',(j,))
                    self.db.execute('UPDATE quota SET used=used-1')
                else:raise Rejected('unknown operation')
                self.db.execute('INSERT INTO audit(operation,arguments) VALUES(?,?)',(operation,json.dumps(args)))
                self.db.execute('RELEASE operation')
                return True,'accepted'
            except Rejected as error:
                self.db.execute('ROLLBACK TO operation');self.db.execute('RELEASE operation')
                return False,str(error)
            except BaseException:
                self.db.execute('ROLLBACK TO operation');self.db.execute('RELEASE operation');raise

    def snapshot(self):
        with self.lock:
            scopes=[];revoked=[]
            for a,issued,rev in self.db.execute('SELECT id,issued,revoked FROM principals ORDER BY id'):
                rights={r[0] for r in self.db.execute('SELECT capability FROM grants WHERE principal=?',(a,))}
                scopes.append(sum(bit for bit,name in CAPS.items() if name in rights))
                revoked.append(bool(rev))
            phases=[PHASES[r[0]] for r in self.db.execute('SELECT phase FROM jobs ORDER BY id')]
            effects=[self.db.execute('SELECT count(*) FROM tool_effects WHERE job=?',(j,)).fetchone()[0] for j in range(len(phases))]
            return dict(scopes=scopes,revoked=revoked,phases=phases,
                        pending=[r[0] for r in self.db.execute('SELECT job FROM obligations ORDER BY job')],
                        used=self.db.execute('SELECT used FROM quota').fetchone()[0],effects=effects,
                        auth=[sum(bit for bit,name in CAPS.items() if self._can(a,name)) for a in range(len(scopes))])

    def unsafe_reserve_at_barrier(self,j,barrier):
        """Seeded implementation race: capacity read is outside the atomic update.
        This method is invoked only by the explicitly unsafe concurrency baseline.
        """
        with self.lock:
            actor,cap,phase=self._job(j)
            permitted=phase=='new' and self._can(actor,cap)
            used,budget=self.db.execute('SELECT used,capacity FROM quota').fetchone()
        barrier.wait(timeout=10)
        if not permitted or used>=budget:return False,'rejected at stale check'
        # Intentionally discard the stale precondition during the write.
        with self.lock:
            self.db.execute('SAVEPOINT race_write')
            try:
                self.db.execute('INSERT INTO obligations VALUES(?)',(j,))
                self.db.execute("UPDATE jobs SET phase='reserved' WHERE id=?",(j,))
                self.db.execute('UPDATE quota SET used=used+1')
                self.db.execute('RELEASE race_write');return True,'accepted after stale read'
            except BaseException:
                self.db.execute('ROLLBACK TO race_write');self.db.execute('RELEASE race_write');raise

class ToolAgent:
    """A scripted actor with a bound principal, not an LLM agent framework."""
    def __init__(self,principal,monitor):self.principal=principal;self.monitor=monitor
    def request(self,operation,job):
        if operation not in ('Reserve','Submit','Commit','CancelConfirmed'):raise ValueError('administrative operation is not exposed to this adapter')
        if self.monitor.config.owners[job]!=self.principal:raise ValueError('agent cannot submit another principal\'s configured job')
        return self.monitor.apply((operation,job))
