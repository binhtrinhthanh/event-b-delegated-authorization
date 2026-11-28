"""Verify reproduced outcomes and summarize elapsed times across ten runs."""
import argparse
import csv
import json
import re
from collections import defaultdict
from pathlib import Path
from statistics import median

parser = argparse.ArgumentParser()
parser.add_argument("checkout", type=Path, help="unchanged checkout of the pinned artifact")
parser.add_argument("--include", nargs="+", choices=("Python/SQLite", "ProB", "Rodin"),
                    default=("Python/SQLite", "ProB", "Rodin"))
args = parser.parse_args()
root = Path(__file__).resolve().parent
groups = defaultdict(list)
raw = []

def load(path):
    return json.loads(path.read_text())

def outcome(obj):
    if isinstance(obj, dict):
        return {key: outcome(value) for key, value in obj.items()
                if key not in ("seconds", "environment")}
    if isinstance(obj, list):
        return [outcome(item) for item in obj]
    return obj

def record(run, tool, configuration, phase, seconds):
    groups[tool, configuration, phase].append(seconds)
    raw.append((run, tool, configuration, phase, seconds))

original = args.checkout / "implementation"
for run in range(1, 11):
    folder = root / f"run-{run:02d}"
    if "Python/SQLite" in args.include:
        main = load(folder / "implementation_results.json")
        local = load(folder / "local_results.json")
        assert outcome(main) == outcome(load(original / "results/implementation_results.json")), folder
        assert outcome(local) == outcome(load(original / "supplement/local_results.json")), folder
        for config in [*main["bounded_conformance"], local["pilot"]]:
            record(run, "Python/SQLite", config["configuration"], "conformance", config["seconds"])
    if "ProB" in args.include:
        for config, result in load(folder / "prob.json").items():
            record(run, "ProB", config, "exploration", result["exploration_seconds"])
            record(run, "ProB", config, "graph_normalization_and_comparison", result["comparison_seconds"])
    if "Rodin" in args.include:
        report = load(folder / "rodin-summary.json")
        assert (report["total"], report["automatic"], report["manual"], report["open"]) == (109, 109, 0, 0)
        log = (folder / "rodin_native.log").read_text()
        components = re.findall(r"^AUTOPROVER_NS (\S+) (\d+)$", log, re.M)
        assert len(components) == 6 and len({name for name, _ in components}) == 6
        for component, ns in components:
            record(run, "Rodin", component, "autoprover", int(ns) / 1e9)
        record(run, "Rodin", "Total", "autoprover", sum(int(ns) for _, ns in components) / 1e9)

with (root / "timings_raw.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("run", "tool", "configuration_or_component", "phase", "seconds"))
    writer.writerows(raw)
with (root / "timings_summary.csv").open("w", newline="") as handle:
    writer = csv.writer(handle)
    writer.writerow(("tool", "configuration_or_component", "phase", "runs", "median_s", "min_s", "max_s"))
    for key, values in groups.items():
        assert len(values) == 10
        row = (*key, len(values), *(f"{t:.6f}" for t in (median(values), min(values), max(values))))
        writer.writerow(row)
        print(*row)
