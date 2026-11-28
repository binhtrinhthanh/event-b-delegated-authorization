# Ten sequential timing repetitions

Artifact source: [commit 413fe35a8ede89add75afe0db4f2e6ccceb95b01](https://github.com/binhtrinhthanh/event-b-delegated-authorization/tree/413fe35a8ede89add75afe0db4f2e6ccceb95b01). The untouched clone passed the 253-file SHA-256 verification before reruns.

Run the three groups sequentially on one host. Each Python/SQLite configuration is measured by the published harness. ProB re-explores the checked Event-B exports included in the pinned commit. Exploration uses the ProB CLI 1.16.1 model-checking wall time; graph normalization and oracle comparison are timed separately after loading the graph. Model export and graph loading are outside the reported phases. Rodin 3.8.0 uses a fresh workspace for every replay and the timed driver included at the pinned commit. The total AutoProver time is computed within each run by summing its per-component elapsed times, before calculating the median and range across runs. Setup, static checking, proof-obligation generation, and evidence collection are outside the timed AutoProver calls.

Run the shell scripts from a disposable checkout because the published runners write their normal result files. Use absolute paths for output directories and tools. The Rodin installation must include the Atelier B Provers core 1.7.1.r16756 and Linux fragment 2.4.0.r16756. Keep an untouched clone for the comparison.

```sh
bash /absolute/evidence/run_python.sh /absolute/evidence
python3 /absolute/evidence/run_prob.py /absolute/unchanged-clone /absolute/ProB/probcli /absolute/evidence
bash /absolute/evidence/run_rodin.sh /absolute/rodin /absolute/ecj.jar /absolute/evidence /absolute/workspaces
python3 /absolute/evidence/summarize.py /absolute/unchanged-clone
```

Each `run-NN` directory contains the recorded logs and outputs. `timings_raw.csv` records every timing and `timings_summary.csv` reports the median, minimum, and maximum by configuration and phase. `environment.txt` records the machine and tool metadata.
