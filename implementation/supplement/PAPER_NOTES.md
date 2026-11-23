# Manuscript integration

## Sections 3.5 and 4.4

The command domain contains four candidate scopes (including the empty scope) per nonroot principal, one revocation command per principal (including the root), and five command types per job. These consist of the four modeled job lifecycle commands and one unsupported release command. This yields 21 candidates per state in the original configurations and 31 in the pilot.

Suggested results text

> We exhaustively explored the pilot with four principals, three jobs, and an allowance of two. The reference monitor agreed with the Python oracle for all 299,026 command trials from 9,646 reachable projected states, including 30,382 accepted and 268,644 rejected commands. We additionally exported the typed Event-B machine to ProB and compared enabled commands and projected successor states with the oracle. Across a chain with allowance one, a star with allowance two, and the pilot, the three implementations of the transition semantics agreed on all 330,106 candidate commands from 11,126 states. The totals are sums across configurations. A candidate command without an enabled Event-B transition was treated as rejected. These results establish bounded agreement under the declared projection and command domains.

Keep the pilot row in Table 5, with totals across all five SQLite configurations of 12,462 states, 358,162 commands, 37,030 accepted commands, and 321,132 rejected commands. Report the subset independently cross-validated by ProB in the text or as a separate column. State that one replay prefix represents each oracle state, and present the two converging-prefix executions as an extra check of that assumption.

## Sections 4.5.1 and 4.5.3

For the two selected model variants, report both the full-hierarchy diagnostics and the concrete reachability goals. ProB reported a Commit simulation error for cached authorization and an invalid variant for unconfirmed release. The respective concrete searches reached a state with `badUse = TRUE` and a state with `submitted ⊈ pending`. The experiments mirror the existing mutations in a copy of the typed model input. Refer to the unchanged Rodin proof results as archived proof evidence.

In the schedule table, use two distinct caller orders for Commit/Commit, two for Commit/CancelConfirmed, and all six permutations for Revoke/Commit/CancelConfirmed. Two of the six permutations commit before the other operations and produce one effect. The other four end with cancellation and no effect. Report the two injection points in the local rollback experiment and that retries leave a single persisted effect under the tested contract.

## Editorial corrections

Map RQ1 to the construction in Section 3.2, RQ2 to Rodin evidence in Section 4.3, and RQ3 to Sections 4.4 and 4.5. Resolve both missing cross-references. State explicitly that the trusted controller may revoke the root and that the adapter permits the configured job owner to abort a pending job after loss of the job's capability. A local abort leaves the original event name in the artifact; any manuscript rename must be applied consistently to figures, tables and notation.
