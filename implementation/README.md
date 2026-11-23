# Executable delegated-authorization case study

This extension supplies scripted release-preparation agents, a SQLite reference monitor, executable local tools, an independent model interpreter, bounded differential tests, seeded implementation faults and native Rodin negative controls.

It is not an integration with an LLM agent framework, external release service, OAuth/MCP server or deployed production system. No API keys or third-party Python packages are required.

## Run the implementation experiments

From the package root:

```bash
python3 implementation/run_experiments.py
```

Outputs are written under `implementation/results/`. This reruns the local workflow, all bounded states and candidate commands in four finite configurations, six seeded faults, controlled concurrent schedules, rollback and adapter checks. The example database is regenerated.

To inspect the actual local tool effects:

```bash
python3 -c "import sqlite3; c=sqlite3.connect('implementation/results/case_study.sqlite'); print(c.execute('SELECT job,tool,result FROM tool_effects').fetchall()); print(c.execute('SELECT job,version FROM release_registry').fetchall())"
```

## Case study and abstraction map

A user delegates a tool-call allowance to a coordinator. The coordinator delegates restricted capabilities to a release agent and an analyst. Read operations retrieve a real local report; publish operations create a local release record. The shared budget counts reserved calls plus calls that have produced effects; it is a lifetime allowance for the workflow, not just a concurrent-request limit.

| Principal | Node | Role |
|---|---:|---|
| User | 0 | Root principal with both capabilities |
| Coordinator | 1 | Parent of nodes 2 and 3; can read reports and delegate |
| Release agent | 2 | Receives releases:publish |
| Analyst | 3 | Receives reports:read |

| Job | Owner | Required capability | Local effect |
|---|---:|---|---|
| 0 | Coordinator | reports:read | Report retrieval and result record |
| 1 | Release agent | releases:publish | Local release-registry record |
| 2 | Analyst | reports:read | Report retrieval and result record |

| Event-B variable/event | Implementation |
|---|---|
| issued, revoked, parent | principals rows |
| scope | grants relation |
| auth | Computed by recursive SQL ancestor traversal and capability membership |
| pending | obligations rows |
| submitted | jobs with phase submitted |
| committed / cancelled | jobs with those phases |
| effectCount(j) | Count of actual tool_effects rows for job j |
| used / budget | quota.used / quota.capacity |
| Delegate / Revoke | Trusted controller operations |
| Reserve / Submit | Job phase transitions through a bound ToolAgent adapter |
| Commit | Revalidate chain, execute local tool and update state in one SQL transaction |
| CancelConfirmed | Atomic local abort removes the staged obligation |

The prototype does not materialize badUse. The independent oracle checks authorization in the pre-state of every accepted use; this is the operational observation corresponding to the history requirement. The deterministic R/T parameters are computed from the pre-state; they are not additional implementation choices.

## Trust boundary and atomicity

The case assumes a fixed acyclic, trusted configuration and authenticated requests reaching one trusted monitor instance. ToolAgent limits job ownership and does not expose administrative operations. This is an in-process adapter, not a Python sandbox; callers capable of arbitrary code or direct database access can bypass it.

A lock serializes monitor operations on one SQLite connection. Savepoints make each operation atomic, including the local database tool effect. A forced tool-insert failure checks that an already inserted release row is rolled back together with monitor state, and a retry creates one effect. This does not establish atomicity across external services, processes or distributed failures.

Submit stages a request. Commit is the effect linearization point. A provider that can independently finish an operation after Submit requires a different environment/reconciliation model. CancelConfirmed is an atomic local abort, not a verified provider-confirmation protocol. The handler checks pending phase and removes the staged operation in the same monitor order; no acknowledgement message or evidence is consumed. See docs/research/STAGED_EXECUTION_CONTRACT.md.

## Independent oracle and finite conformance

`oracle.py` is a pure immutable Python interpretation of M2, manually constructed from the shipped model. It does not import monitor logic or execute SQLite. The implementation uses SQL tables/recursive queries; the oracle uses mathematical ancestor sets, bitsets and tuple states.

For every reachable oracle state, the harness reaches the implementation state by replaying a shortest accepted prefix. It then tests every candidate command, checks enabledness and projected post-state, checks fixed safety requirements, and rolls the trial back. Rejected operations must leave state unchanged. The command domain includes all nonroot delegation targets with scope masks 0–3, all revocation targets and all job IDs for the four lifecycle operations, plus a rejected unconfirmed-release command. This is exhaustive only for each declared finite configuration and command domain.

This is empirical conformance to an independent Python interpretation, not a proof that Python code refines Event-B. The oracle-to-Event-B correspondence is documented manually and has not been mechanically proved or cross-validated with ProB.

## Seeded faults

The unchanged oracle/requirements are used for correct and faulty monitors. Six deliberately seeded variants remove scope attenuation, ignore ancestor revocation, omit Commit revalidation, omit the shared-budget guard, release unconfirmed obligations or allow replayed Commit. An additional separate race baseline reads capacity before the serialized write. These are constructed negative controls, not independently collected real defects; detection rates do not estimate real-world effectiveness.

The safe/unsafe concurrency comparison deliberately controls schedules. It tests two requests at capacity one, not a production throughput benchmark or all possible thread interleavings. Revocation tests cover both selected linearization orders.

## Native model negative controls

```bash
python3 implementation/check_model_mutants.py --rodin /absolute/path/to/rodin --ecj /absolute/path/to/ecj.jar
```

The ECJ argument can be omitted if javac is installed. Atelier B Provers is required, as for the verified baseline. Each source variant retains all invariants, base contexts and abstract M0/M1, and mutates concrete M2/M3. It must statically check, then leave relevant M2 obligations open. Generated sources, logs and PO goals are under `implementation/model_mutants/`.

An undischarged PO alone is not a demonstrated bug. The package pairs native negative-control results with concrete prototype traces violating the unchanged oracle/requirements. These traces are not claimed to be counterexamples generated by ProB; native animation remains outstanding. The model and implementation mutations represent matching fault mechanisms but are not proved bisimilar variants.
