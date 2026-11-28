# Formal Verification of Delegated Authorization in Agentic Workflows with Staged Execution

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
| Converging-history assessment on two configurations | 1,339 states, 8,994 prefixes, and 188,874 single-command trials with no mismatches |
| Deeper branching configuration | 12 selected traces and 156 command trials, with no mismatches |
| Reachable violation states found by ProB | 6/6 Event-B variants (2 original and 4 supplementary) |
| Seeded implementation faults detected | 6/6 |
| Native negative-control model variants | 6, with 1, 1, 2, 1, 4 and 3 open obligations in the order listed below |

The baseline proof result uses Rodin 3.8, Atelier B Provers and the supplied
`DelegatedAuto` profile. The six negative controls are scope expansion,
local revocation, cached authorization, missing budget check, early release
and replayed commit. Rodin reports their open obligations separately.
ProB reached violation states for cached authorization and early release in
the [original experiments](implementation/supplement/native_results/) and for
scope expansion, local revocation, missing budget check, and replayed commit
in the [supplementary searches](implementation/supplement/additional_evaluation/additional_goals/).

### Reproduction check

The results below come from ten sequential repetitions per tool on Linux
x86_64 with an Intel Xeon Platinum 8573C, nine visible logical CPUs, and
approximately 9.7 GiB of visible RAM. The runs used Python 3.12.14,
SQLite 3.53.1, OpenJDK 21.0.13.1, Rodin 3.8.0 with Atelier B Provers,
and ProB CLI 1.16.1. Each Rodin repetition used a fresh workspace.
Every repetition reproduced the published proof inventory or the
corresponding conformance results.

| Configuration | Python/SQLite (s) | ProB exploration (s) | ProB graph comparison (s) |
|---|---:|---:|---:|
| Chain, budget 1 | 1.03 [0.96–1.58] | 0.324 [0.286–0.618] | 0.037 [0.033–0.080] |
| Chain, budget 2 | 1.37 [1.33–2.17] | — | — |
| Star, budget 1 | 1.77 [1.73–2.20] | — | — |
| Star, budget 2 | 2.49 [2.42–2.94] | 0.572 [0.538–0.849] | 0.092 [0.088–0.191] |
| Pilot, budget 2 | 37.06 [36.05–42.20] | 3.073 [2.860–3.577] | 1.042 [0.992–1.337] |

Each cell reports the median [minimum–maximum]. ProB exploration uses the
reported model-checking wall time. Graph comparison includes normalization
and oracle comparison. The ProB runs use the archived Event-B exports.
Model export and graph loading are outside the measured phases. Rodin's
total AutoProver time was 31.94 [26.81–40.00] s, calculated by summing
unrounded component times within each repetition before computing the
summary. See the [timing protocol and logs](implementation/supplement/timing-evidence/)
and the [timing summary CSV](implementation/supplement/timing-evidence/timings_summary.csv).

## Supplementary material

The supplementary PDF accompanying the manuscript presents the two
Event-B contexts and four refinement machines. The corresponding Rodin
files are in [`DelegatedAuthorization/`](DelegatedAuthorization/) and
the proof and experiment evidence is available in the directories below.

## Repository contents

| Path | Contents |
|---|---|
| `DelegatedAuthorization/` | Native contexts, machines, saved proofs and project settings |
| `model_spec.json` | Model specification used by the generator |
| `implementation/` | Reference monitor, independent Python oracle and experiment harness |
| `implementation/results/` | Raw JSON/CSV results, logs and example SQLite database |
| `implementation/supplement/` | Pilot, ProB comparison, interleavings, rollback, raw evidence and manuscript notes |
| `implementation/supplement/timing-evidence/` | Ten timing repetitions, logs, scripts, and summary CSV |
| `implementation/supplement/additional_evaluation/` | Deeper-branch traces and four supplementary ProB witnesses |
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

For the [converging-history assessment](implementation/supplement/CONVERGING_HISTORIES.md), run:

```bash
python3 implementation/supplement/check_converging_histories.py --output /tmp/converging_histories_results.json
```

This supplementary assessment includes trials that overlap the single-prefix assessment. Its count is reported separately.

For the native Event-B comparison and two model-variant witnesses, follow the
[ProB reproduction instructions](implementation/supplement/README.md). The
three configurations compared in ProB are part of the five SQLite configurations.
See the [additional evaluation instructions](implementation/supplement/additional_evaluation/README.md)
for the deeper branching traces and four further ProB witnesses.

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

The [clean replay evidence](validation/rodin_clean_replay/README.md) records the regenerated 109 proofs. The clean runner imports source contexts and machines without saved proofs. Use a JDK, or pass `--ecj /absolute/path/to/ecj.jar` if the Java compiler is unavailable. Native negative controls can be regenerated with:

```bash
python3 implementation/check_model_mutants.py --rodin /absolute/path/to/rodin
```

See [docs/PROOF_GUIDE.md](docs/PROOF_GUIDE.md) and [docs/README_VI.md](docs/README_VI.md) for details.

## Scope and interpretation

The model covers a fixed rooted delegation tree, capability attenuation, cascading irreversible revocation, unit-cost shared budget and a staged job lifecycle. `Submit` does not dispatch an external operation. `Commit` rechecks authority and performs a protected local SQL effect atomically with monitor updates. `CancelConfirmed` is a local abort, not a verified remote cancellation acknowledgement.

The prototype assumes one trusted monitor, authenticated requests, complete mediation and protected configuration/database access. It is not a sandbox, deployed agent framework or distributed provider protocol. The independent Python oracle is manually derived; code refinement to Event-B has not been formally proved. Bounded conformance applies to the five declared SQLite configurations and the specified state projections and command domains. The native ProB comparison covers three of these configurations. The six ProB witnesses concern the seeded Event-B variants.

See [docs/SEMANTICS.md](docs/SEMANTICS.md), [the execution contract](docs/research/STAGED_EXECUTION_CONTRACT.md), and [the experimental report](docs/IMPLEMENTATION_RESULTS_VI.md).

## Integrity

`SHA256.json` records the published artifact hashes, including the timing evidence. Verify them using:

```bash
python3 tools/verify_manifest.py
```

Install Rodin and Atelier B for proof replay, and ProB CLI and the ProB2-UI Java archive for the ProB experiments.
