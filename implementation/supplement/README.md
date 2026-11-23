# Supplementary experiments for delegated authorization

This supplement uses the monitor, oracle, and Event-B sources from the GitHub archive. The three implementation archives have byte-identical monitor, oracle, and experiment runner files. The four archives containing Rodin projects have byte-identical baseline .bum and .buc files. The separate legacy experiment uses a different Python model with read-only jobs, so its results are reported separately.

## Reproduce

Run from the root of the extracted package with Python 3.12 or later.

```sh
python3 implementation/run_experiments.py
python3 implementation/supplement/run_local.py
python3 implementation/supplement/run_native.py /path/to/probcli /path/to/prob2-ui-1.4.0-linux.jar
```

The native experiment used ProB CLI 1.16.1, the ProB2-UI 1.4.0 Java archive, and Java 21. For Linux, the Java archive is under `opt/prob2-ui/lib/app/` in the official ProB2-UI Debian package. The script exports the Rodin checked machine through the ProB Event-B API. If the exports are already present, ProB CLI alone is enough to model-check those files. See the saved per-configuration logs for the exploration results.

- [ProB downloads](https://prob.hhu.de/w/index.php/Download)
- [ProB CLI guide](https://prob.hhu.de/w/index.php/Using_the_Command-Line_Version_of_ProB)

Run the manifest check before rerunning experiments. The baseline runner replaces its original JSON and SQLite result files. The supplement runners regenerate their own result files. Timings, solver state identifiers, paths and compressed file bytes can change across runs.

## Results

| Configuration | Reachable domain states | Enabled transitions | Candidate commands | Rejected / disabled commands |
|---|---:|---:|---:|---:|
| Chain, allowance 1 | 422 | 882 | 8,862 | 7,980 |
| Star, allowance 2 | 1,058 | 2,691 | 22,218 | 19,527 |
| Pilot, allowance 2 | 9,646 | 30,382 | 299,026 | 268,644 |
| Total | 11,126 | 33,955 | 330,106 | 296,151 |

These configurations agree on command enabledness and projected successor state across Event-B in ProB, the Python oracle and the SQLite monitor. For ProB, a rejected command is represented by absence of an enabled transition after projection. The SQLite monitor also preserves the projected state on rejection. The graph comparator excludes constant setup and initialization from the domain counts. The SQLite implementation assessment uses one representative prefix per oracle state, so the scope is the explored finite domain and the declared projection.

The pilot export uses the original Rodin checked model. The small instances reuse the same machine and specialize the finite context in copies of the checked XML for animation. In particular, the event guards, actions and invariants stay the same in these copies. The pilot witnesses cover authorized commit and rejection after ancestor revocation followed by cancellation. ProB graph setup and initialization add bookkeeping transitions to the CLI totals.

The two negative controls mirror the archived model edits in an animation copy of the checked XML. Running the full hierarchy reports a simulation diagnostic for cached authorization and a variant diagnostic for early release. A second run explicitly checks reachability of each reversed safety predicate with zero animated abstraction levels. It reaches `badUse = TRUE` for cached authorization and `not(submitted <: pending)` for early release. The Rodin proof results remain the archived evidence. This procedure does not regenerate proof obligations or discharge them.

## Local execution

- The pilot conformance run exhausts all 9,646 oracle states and accepts 30,382 of its 299,026 candidate commands. All four original Table 5 configurations reproduce, giving 12,462 states and 358,162 checks across the five SQLite configurations.
- The five-principal scenario exercises one independent branch after revocation in another. The monitor keeps the revoked job's reservation, rejects its commit, and denies a valid job in the other branch while allowance is full. The valid job can reserve immediately after the revoked reservation is cancelled.
- Two issuance prefixes with swapped sibling order reach the same projection. Seven subsequent commands agree through the job adapter with normal SQLite transaction commits.
- Ten forced caller orders cover two competing commit callers, both commit/cancel orders, and six revoke/commit/cancel permutations. The two commit callers have identical command content and distinct caller identities. The lock test wraps the original monitor lock to control entry order. It validates the serial outcomes against the oracle and checks actual release rows.
- The original injected failure before insertion into the tool-effect table and the added failure after the ledger updates both roll back. The late case independently reads the file-backed database after the exception. Retry persists one tool effect and one release row, and a repeated commit is rejected.
- The root-revocation trace disables commit while preserving the ability to cancel the already submitted job.

## Evidence files

- `baseline_rerun.json` contains the rerun summary for Tables 5–8 and the archived Rodin metadata.
- `legacy_rerun.json` records the separate Python-only experiment. Its 12 baseline configurations and six negative controls replicate the archived state counts, transitions and verdicts.
- `local_results.json` contains the new bounded assessment and individual SQLite traces.
- `native_results/summary.json` contains the ProB graph comparison and both native negative controls. Each directory includes the exported Event-B package, run log, and either a compressed graph or trace files.

The original GitHub archive's manifest identified one mismatch before rerunning anything. `validation/finite_validation.json` had equivalent data except for per-run timing values. The identical file from the Rodin bundle that matches the original checksum is used here. The baseline artifacts in the package preserve their archived results. Fresh baseline summary results are included in this supplement.
