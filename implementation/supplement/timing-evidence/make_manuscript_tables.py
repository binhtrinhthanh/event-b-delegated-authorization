"""Generate replacement timing cells from the verified summary."""
import csv
from pathlib import Path

root = Path(__file__).resolve().parent
with (root / "timings_summary.csv").open(newline="") as handle:
    timings = {(row["tool"], row["configuration_or_component"], row["phase"]): row
               for row in csv.DictReader(handle)}

def cell(tool, name, phase, digits):
    row = timings[tool, name, phase]
    median, minimum, maximum = (f"{float(row[key]):.{digits}f}" for key in
                                ("median_s", "min_s", "max_s"))
    return f"{median} [{minimum}--{maximum}]"

rows = [
    "% Replacement columns for Tables 6--8. Every entry is median [min--max].",
    "% Keep the existing count columns. Rodin rows C_Pilot and M3_Pilot have no POs.",
    "% Table 6: AutoProver time (s)",
]
for name in ("C_Delegation", "M0_AuthorityLedger", "M1_DelegationChain",
             "M2_SubmittedObligations", "Total"):
    rows.append(f"% {name}: {cell('Rodin', name, 'autoprover', 2)}")
rows.append("% Table 7: Python/SQLite wall time (s)")
for name in ("chain_budget1", "chain_budget2", "star_budget1", "star_budget2", "pilot_budget2"):
    rows.append(f"% {name}: {cell('Python/SQLite', name, 'conformance', 2)}")
rows.append("% Table 8: ProB exploration (s) and comparison (s)")
for name in ("chain_budget1", "star_budget2", "pilot_budget2"):
    exploration = cell("ProB", name, "exploration", 3)
    comparison = cell("ProB", name, "graph_normalization_and_comparison", 3)
    rows.append(f"% {name}: {exploration} & {comparison}")
(root / "manuscript_timing_cells.tex").write_text("\n".join(rows) + "\n")
