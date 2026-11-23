# Semantics and assumptions

The detailed manuscript contract and assumption/evidence boundaries are in research/STAGED_EXECUTION_CONTRACT.md. This file interprets the existing sources without changing the model or proofs.

The root is a user principal; nonroot nodes are agents/delegated credentials. The topology is a finite fixed rooted tree, with strictly decreasing rank along parent edges and an explicit ancestor path including the node and root. Each node can be issued at most once; revocation is irreversible. Agent scheduling and enabled actions are nondeterministic; LLM correctness is not assumed.

A trusted atomic reference monitor mediates all Reserve, Submit and Commit actions. Authentication, authentic messages and non-bypassability of this monitor are assumptions. A proof of its implementation or of a cryptographic delegation protocol is outside this model.

Capabilities are abstract action/resource permissions. owner(j) identifies the executor and need(j) the required capability. Scope is a relation NODE↔CAP; scope[{a}] gives a's capabilities. dom(scope)=issued and all issued scopes are nonempty. Descendant scopes are subsets of immediate parent scopes and of rootScope.

`auth = scope ∩ {x,k · x∈NODE ∧ k∈CAP ∧ path(x)∩revoked=∅ ∣ x↦k}`. Revoke recomputes auth atomically, invalidating use by all descendants. It does not erase historical effects or release existing obligations. Commit rechecks auth even for an earlier submitted job.

Submit stages a request without an irreversible external effect. Commit is the linearization point of the effect. If an external provider can independently complete a previously submitted request after revocation, an environment/reconciliation refinement is needed; that behavior is not established safe by this model.

CancelConfirmed is enabled for pending reservations even after revocation. In the prototype it is an atomic local abort of a staged job; it does not verify a provider acknowledgement or remote reconciliation evidence. Interpreting its name as external confirmation would be an additional environmental assumption requiring a further refinement. It cannot occur after Commit. Here a resource obligation means a held unit reservation, not a deontic policy obligation or an independently incurred external liability. Each job consumes one resource unit. `used = card(pending)+card(committed)` records pending obligations plus historical consumption; `used≤budget` is the shared bound.

M0 specifies the ledger and nondeterministic abstract authority changes. M1 refines authority changes into Delegate/Revoke and proves chain/scope invariants. M2 introduces submitted⊆pending, an operational effectCount counter, and badUse history monitoring. Submit refines skip and is convergent with variant card(pending∖submitted). Every other event refines its namesake, except Delegate/Revoke which refine SetAuthority.

badUse is updated from pre-state authorization on Reserve/Submit/Commit and stays FALSE. It does not require previously committed jobs to remain authorized after later revocation. effectCount is incremented at Commit; it stays ≤1 and is characterized by committed membership.

R and T are uniquely defined event parameters naming remainders. The structural/cardinality facts used about them are theorem guards whose THM and WD obligations are included in the native proof inventory.

C_Pilot/M3_Pilot instantiate one user, three agents, two capabilities, three jobs and budget=2. The generic model is not restricted to this instance. An explicit Python witness satisfies all sixteen base context axioms; zero static errors alone would not establish context consistency.

Not modeled: weighted requests, per-child budgets, expiry, credential renewal, asynchronous revocation propagation, crashes, token audience binding or bypasses of the trusted monitor. At-most-once is safety; exactly-once delivery, fairness, eventual completion and deadlock freedom are not claimed. No ProB/deployed-agent experiment is included.
