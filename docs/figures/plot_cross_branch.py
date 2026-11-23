"""Render the three checkpoints of the recorded cross-branch scenario."""
import json
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

HERE = Path(__file__).resolve().parent
TRACE = HERE.parents[1] / "implementation/supplement/local_results.json"


def main():
    rows = json.loads(TRACE.read_text())["cross_branch"]
    before, revoke, commit, denied, cancel, retry = rows[-6:]
    assert [row["command"] for row in rows[-6:]] == [
        ["Reserve", 1], ["Revoke", 1], ["Commit", 0], ["Reserve", 2],
        ["CancelConfirmed", 0], ["Reserve", 2],
    ]
    assert [row["accepted"] for row in rows[-6:]] == [True, True, False, False, True, True]
    assert revoke["state"]["auth"][2] == 0 and revoke["state"]["auth"][4] == 1
    assert [row["state"]["pending"] for row in (before, denied, cancel, retry)] == [
        [0, 1], [0, 1], [1], [1, 2],
    ]
    assert [row["state"]["used"] for row in (before, denied, cancel, retry)] == [2, 2, 1, 2]

    panels = [
        ("Before revocation", [
            "Job 0 is submitted.",
            "Job 1 holds a reservation.",
            "Pending jobs: 0, 1",
            "Used allowance: 2 / 2",
        ]),
        ("After Revoke(1)", [
            "Commit(0) rejected: authority revoked.",
            "Reserve(2) rejected: allowance full.",
            "Pending jobs: 0, 1",
            "Used allowance: 2 / 2",
        ]),
        ("After CancelConfirmed(0)", [
            "Cancellation frees one unit.",
            "Reserve(2) succeeds on retry.",
            "Pending jobs after retry: 1, 2",
            "Used allowance: 1 / 2 to 2 / 2",
        ]),
    ]
    fig, ax = plt.subplots(figsize=(10, 2.75))
    ax.set(xlim=(0, 10), ylim=(0, 2.75))
    ax.axis("off")
    ax.text(0.1, 2.61, "Delegation paths and job ownership", fontsize=10, fontweight="bold")
    ax.text(0.1, 2.33, "Root → coordinator 1 → agent 2 (job 0), agent 3", fontsize=10)
    ax.text(0.1, 2.08, "Root → independent agent 4 (jobs 1 and 2)", fontsize=10)
    colors = ["#edf3f8", "#fff0e5", "#eaf6f0"]

    for i, ((title, lines), color) in enumerate(zip(panels, colors)):
        x = 0.1 + 3.35 * i
        ax.add_patch(FancyBboxPatch((x, 0.12), 3.05, 1.65,
                                    boxstyle="round,pad=0.03,rounding_size=0.09",
                                    facecolor=color, edgecolor="#556575", linewidth=0.65))
        ax.text(x + 0.12, 1.53, title, fontsize=10, fontweight="bold", color="#142337")
        for j, line in enumerate(lines):
            ax.text(x + 0.12, 1.24 - 0.27 * j, line, fontsize=9.2, color="#142337")
        if i < 2:
            ax.annotate("", xy=(x + 3.32, 0.94), xytext=(x + 3.08, 0.94),
                        arrowprops={"arrowstyle": "->", "color": "#556575", "lw": 1})
    fig.subplots_adjust(left=0, right=1, bottom=0, top=1)
    fig.savefig(HERE / "cross_branch_revocation.pdf")
    plt.close(fig)


if __name__ == "__main__":
    main()
