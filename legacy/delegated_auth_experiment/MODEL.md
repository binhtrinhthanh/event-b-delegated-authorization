# Delegated authorization: formal model and Event-B translation plan

Status: executable finite transition system in experiment.py. This document is a mathematical specification and translation plan, NOT a Rodin-importable project or a discharged proof.

## Scope and trust boundary
A trusted reference monitor mediates every Reserve, Submit and Commit. Agents choose arbitrary enabled actions; neither LLM accuracy nor cooperation is assumed. The root is a user principal, other nodes are agents. The parent tree is fixed and acyclic. Credential identities, authentic messages and atomic monitor events are assumptions. This is not an OAuth/MCP implementation, a cryptographic protocol proof, or an experiment on deployed agents.

Capabilities are subsets of {read, write}. The root initially has {read}; delegated capabilities must be subsets of the parent's. Jobs exercise read capability and consume one abstract resource unit. Resource units could denote tool-call allowance, document-access allowance, or monetary commitments. These labels do not constitute separate benchmarks.

## State and mathematical invariants
Fixed sets: N nodes, J jobs. parent maps each nonroot to an earlier node. owner maps jobs to nonroot nodes. B is the root's shared resource allowance.

Variables: scope ∈ N → POW({read,write}); issued ⊆ N; revoked ⊆ N; phase ∈ J → {new,reserved,submitted,paid,cancelled}; held ∈ J → {0,1}; paid ∈ J → {0,1,2}.

Python encodes unissued as scope=0, combines issued and scope, and disallows issuing an empty capability. Each node can be issued at most once. paid=2 is reachable only in a mutant.

live(a) ≜ a∈issued ∧ a∉revoked ∧ ∀p∈ancestors(a)·p∈issued ∧ p∉revoked.
authorized(a) ≜ live(a) ∧ read∈scope(a).

Safety requirements:
1. Scope attenuation: ∀a∈issued\{root}·scope(a) ⊆ scope(parent(a)).
2. Shared resource bound: Σj paid(j) + Σj held(j) ≤ B.
3. At-most-once effect: ∀j·paid(j) ≤ 1. This is NOT exactly-once/liveness.
4. Obligation coverage: phase(j)∈{reserved,submitted} ⇒ held(j)=1.
5. Authorization at use: Reserve(j), Submit(j), Commit(j) require authorized(owner(j)) in their PRE-state.

Requirement 5 is a transition property. For Event-B, introduce ghost `unauthorizedUse` initialized FALSE, update it on each use event with the pre-state authorization predicate, and prove unauthorizedUse=FALSE. Do not assert that all previously paid jobs must retain live authorization: historical effects remain legitimate after later revocation.

## Events and guards
INITIALISATION: root issued with read, no revocation, jobs new, all held/paid zero.
Delegate(p,a,S): a unissued; p=parent(a); live(p); ∅≠S⊆scope(p). Set issued(a), scope(a)=S.
Revoke(a): a issued and not revoked. Add a to revoked. Outstanding obligations remain accounted for.
Reserve(j): phase=new; authorized(owner(j)); Σpaid+Σheld<B. Set phase=reserved, held=1.
Submit(j): phase=reserved; authorized(owner(j)). Set phase=submitted.
Commit(j): phase=submitted; authorized(owner(j)); held(j)=1. Set phase=paid, held=0, paid=paid+1 atomically.
CancelConfirmed(j): phase reserved or submitted. External cancellation/reconciliation is assumed complete at this event. Set cancelled, held=0.

No new use is allowed following effective revocation of any ancestor. A reservation may remain pending after revocation until CancelConfirmed. There is no guarantee of cancellation, eventual completion, exactly-once delivery, expiry, bounded revocation propagation, or crash recovery.

## Intended Event-B development (not yet executed)
C0: finite node/job domains, fixed acyclic parent relation, ownership, positive B.
M0: abstract atomic authorized resource use and shared allowance.
M1: delegated scopes, revocation, ancestor closure, ghost unauthorizedUse.
M2: reservation/submission/commit/cancellation and obligation accounting.

These are candidate refinement layers. Refinement mappings, gluing invariants, status of new events, variants and concrete proof obligations must be developed and checked in Rodin; refinement compatibility is not established by the Python runs. In particular, reservation accounting needs an explicit abstract reserved-resource variable or a suitable abstract allocation event, rather than an unproved claim that Reserve refines skip.

## Mutation operators
scope_expansion: remove subset guard on Delegate.
local_revocation: inspect only immediate credential at use, ignoring ancestors.
cached_authorization: omit revalidation at Commit.
no_shared_budget: omit global capacity guard at Reserve.
early_release: add ReleaseBeforeCancel on submitted obligation.
replay_commit: permit a second effect after paid.

Every mutant is checked against unchanged requirements. BFS stops at the first failing edge and exports a shortest counterexample by event count. Reported mutant states/transitions count only exploration before failure, not complete mutant state spaces.
