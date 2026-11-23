# Formal Verification of Delegated Authorization in Agentic Systems

Replication package containing Event-B/Rodin models, automatic proof evidence, a Python/SQLite reference monitor, and reproducible experiments for a centralized staged authorization workflow.

## Recorded results

| Evaluation | Recorded result |
|---|---:|
| Baseline Rodin proof obligations | 109/109 automatically discharged |
| Manual / open baseline obligations | 0 / 0 |
| Original bounded SQLite runs | 2,816 states and 59,136 command trials |
| Pilot SQLite run | 9,646 states and 299,026 command trials |
| All five SQLite configurations | 12,462 states and 358,162 command trials |
| ProB–oracle–SQLite comparison on three of the five configurations | 11,126 states and 330,106 command trials, with no mismatches |
| Controlled caller orders checked | 10 |
| ProB negative-control witnesses | 2 |
| Seeded implementation faults detected | 6/6 |
| Native negative-control model variants | 6 |

The proof result uses Rodin 3.8, Atelier B Provers and the supplied `DelegatedAuto` profile. It is not a result for every default Rodin configuration. Negative-control projects intentionally contain open obligations and are excluded from the baseline total.

## Repository contents

| Path | Contents |
|---|---|
| `DelegatedAuthorization/` | Native contexts, machines, saved proofs and project settings |
| `model_spec.json` | Model specification used by the generator |
| `implementation/` | Reference monitor, independent Python oracle and experiment harness |
| `implementation/results/` | Raw JSON/CSV results, logs and example SQLite database |
| `implementation/supplement/` | Pilot, ProB comparison, interleavings, rollback, raw evidence and manuscript notes |
| `validation/rodin_clean_replay/` | Fresh Rodin project, log, PO inventory and source hashes |
| `docs/approach-figure/` | Editable approach figure and rendered exports |
| `docs/figures/` | Cross-branch revocation figure and trace-based renderer |
| `legacy/delegated_auth_experiment/` | Earlier Python-only model and recorded results |
| `implementation/model_mutants/` | Six native negative-control projects and evidence |
| `validation/` | Native baseline logs, PO inventory and summaries |
| `tools/` | Model generation, checking and headless proof tooling |
| `plugins/` | Supplied automatic tactic plugin, with source under `tools/headless/` |
| `docs/` | Readable model, semantics, proof guide and experimental reports |

## Reproduce the implementation experiments

Use Python 3.10 or newer with SQLite and the standard library. No API keys, LLM service or third-party Python packages are needed.

```bash
python3 implementation/run_experiments.py
```

This overwrites the generated implementation results and example database. Run in a fresh checkout to retain the recorded evidence. Timings and environment metadata depend on the host. See [implementation/README.md](implementation/README.md) for domains, scenarios and limitations.

For the pilot, controlled caller orders and late rollback, run:

```bash
python3 implementation/supplement/run_local.py
```

For the native Event-B comparison and two model-variant witnesses, follow the
[ProB reproduction instructions](implementation/supplement/README.md). The
three configurations compared in ProB are part of the five SQLite configurations.

Additional model checks:

```bash
python3 tools/check_sources.py
python3 tools/check_context.py
python3 tools/check_finite.py
```

These checks supplement native proofs; they are not ProB model checking.

## Open and re-prove the model

1. Install Rodin 3.8 and Atelier B Provers from https://www.atelierb.eu/update_site/atelierb_provers/.
2. Copy `plugins/delegated.batch_1.0.0.jar` into Rodin's `dropins` directory and restart Rodin.
3. Import `DelegatedAuthorization/` using **File → Import → General → Existing Projects into Workspace**.
4. Check that the project uses the `DelegatedAuto` prover profile, then run automatic proof.

For a clean Linux headless run, with a fresh absolute work directory:

```bash
python3 tools/run_rodin.py --rodin /absolute/path/to/rodin --work /absolute/path/to/new-work
python3 tools/collect_evidence.py --workspace-project /absolute/path/to/new-work/workspace/DelegatedAuthorization --native-log /absolute/path/to/new-work/rodin_native.log
```

The [clean replay evidence](validation/rodin_clean_replay/README.md) records the regenerated 109 proofs. The clean runner imports source contexts and machines without saved proofs. A JDK is required; alternatively pass `--ecj /absolute/path/to/ecj.jar`. Native negative controls can be regenerated with:

```bash
python3 implementation/check_model_mutants.py --rodin /absolute/path/to/rodin
```

See [docs/PROOF_GUIDE.md](docs/PROOF_GUIDE.md) and [docs/README_VI.md](docs/README_VI.md) for details.

## Scope and interpretation

The model covers a fixed rooted delegation tree, capability attenuation, cascading irreversible revocation, unit-cost shared allowance and a staged job lifecycle. `Submit` does not dispatch an external operation. `Commit` rechecks authority and performs a protected local SQL effect atomically with monitor updates. `CancelConfirmed` is a local abort, not a verified remote cancellation acknowledgement.

The prototype assumes one trusted monitor, authenticated requests, complete mediation and protected configuration/database access. It is not a sandbox, deployed agent framework or distributed provider protocol. The independent Python oracle is manually derived; code refinement to Event-B has not been formally proved. Bounded conformance applies to the five declared SQLite configurations and the specified state projections and command domains. The native ProB comparison covers three of these configurations. The two ProB witnesses concern selected synthetic model variants.

See [docs/SEMANTICS.md](docs/SEMANTICS.md), [the execution contract](docs/research/STAGED_EXECUTION_CONTRACT.md), and [the experimental report](docs/IMPLEMENTATION_RESULTS_VI.md).

## Integrity

`SHA256.json` records the published artifact hashes. Verify them using:

```bash
python3 tools/verify_manifest.py
```

Install Rodin and Atelier B for proof replay, and ProB CLI and the ProB2-UI Java archive for the ProB experiments.
