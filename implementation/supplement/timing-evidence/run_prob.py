"""Rerun native exploration and oracle comparison from the published exports."""
import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from tempfile import TemporaryDirectory
from time import perf_counter

parser = argparse.ArgumentParser()
parser.add_argument("checkout", type=Path)
parser.add_argument("probcli", type=Path)
parser.add_argument("output", type=Path)
args = parser.parse_args()
supplement = args.checkout.resolve() / "implementation/supplement"
sys.path.insert(0, str(supplement))
from run_native import CONFIGS, compare_graph, normalize_graph

exports = supplement / "native_results"
expected = json.loads((exports / "summary.json").read_text())
for run in range(1, 11):
    output = args.output / f"run-{run:02d}"
    output.mkdir(parents=True, exist_ok=True)
    results = {}
    for name, config in CONFIGS.items():
        model = exports / name / "model.eventb"
        with TemporaryDirectory() as temp:
            graph = Path(temp) / "graph.dot"
            invocation = [
                str(args.probcli.resolve()), str(model), "-model_check", "-nodead",
                "-p", "MAX_OPERATIONS", "1000", "-dot", "state_space", str(graph),
            ]
            with (output / f"prob-{name}.log").open("w") as log:
                subprocess.run(invocation, stdout=log, stderr=subprocess.STDOUT,
                               cwd=temp, check=True, timeout=180)
            log_text = (output / f"prob-{name}.log").read_text()
            assert "No counter example found. ALL states visited." in log_text
            timing = re.search(r'Model checking time: .*?\(([\d.]+)\s*(ms|s) walltime\)', log_text)
            assert timing, log_text
            elapsed = float(timing[1]) / (1000 if timing[2] == "ms" else 1)
            raw = graph.read_text()
            start = perf_counter()
            observed = compare_graph(config, normalize_graph(raw))
            comparison = perf_counter() - start
        assert json.loads(json.dumps(observed)) == expected[name], (name, observed)
        results[name] = dict(exploration_seconds=elapsed, comparison_seconds=comparison, **observed)
    (output / "prob.json").write_text(json.dumps(results, indent=2) + "\n")
    print(f"ProB {run:02d} done", flush=True)
