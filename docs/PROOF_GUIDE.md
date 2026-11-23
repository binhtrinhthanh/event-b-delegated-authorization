# Proof review guide

The supplied native inventory has 109/109 automatically discharged obligations. A green source file requires accurate static checking; this alone is not a discharged proof. Use the Rodin proof-obligation view and retain both open and discharged obligations.

## Main goals
- M0 Reserve/inv09 and /inv10: use j outside all ledger sets, finite JOB, cardinality of a fresh singleton union, and used<budget.
- M0 Commit/inv09: pending and committed are disjoint, j is pending, so removal and insertion conserve the sum of cardinalities.
- M0 CancelConfirmed/inv08 and /inv09: j pending implies card(pending)≥1, and cancellation reduces used by exactly one.
- M1 Delegate/inv16: split new issued element a from old issued nodes; use path(a)={a}∪path(parent(a)) and the parent's ancestor-closure invariant.
- M1 Delegate/inv17 and /inv18b: split the newly issued credential from old ones, use the relational extension scope∪({a}×S) on fresh domain element a and the parent's scope bound.
- M1 Delegate/inv19: substitute P and the new issued/scope state.
- M1 Revoke/inv19: substitute P and revoked∪{a}. Do not add an invariant requiring historical committed jobs to remain authorized.
- M1 Delegate/SetAuthority guard strengthening: the comprehension is a subset of NODE×CAP by the issued/scope typing invariants.
- M2 Submit/VAR: j∈pending∖submitted, finite(pending), and singleton insertion into submitted strictly reduces pending∖submitted.
- M2 Commit/inv22a and /inv22b: j is pending and not committed; the counter increases from 0 to 1, while committed gains j. All other counters remain unchanged.
- M2 Commit/inv23: use inv22b and the pre-state disjointness of pending and committed; do not add effectCount(j)=0 as an unexplained guard merely to hide replay.
- M2 Reserve/Submit/Commit inv25: the authorization guard makes the bool argument FALSE when badUse=FALSE. inv19 establishes the chain-revocation meaning of the authorization guard.

## Audit evidence
Report the actual PO inventory, discharged/open status, automatic/manual procedure, Rodin version and prover configuration. The source's number of invariants or events is not a PO count. Export the native .bpr proof files with the corresponding unchanged sources.

Mutations should keep requirements fixed: remove attenuation on Delegate; drop ancestor revocation checking; drop Commit revalidation; drop Reserve capacity check; allow early cancellation release while obligation remains; allow repeated effect. A failed or open PO alone does not establish an executable counterexample: confirm suspect mutations by animation/model checking or trace replay.

## Automatic strategy

The shipped version uses the native AutoProver with profile DelegatedAuto and Atelier B Provers; all .bps manual flags are false. The supplementary R/T partition and cardinality guards have theorem=true and their THM/WD obligations are included. Contextual equality rewriting uses native Eq/LocalEqRewrite reasoners, followed by native rewriting and prover calls. No Review, custom proof oracle or PO-specific branch is used.
