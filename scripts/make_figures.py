"""Draw the README figures from results/*.json.

Optional: needs matplotlib (pip install matplotlib). The analyses themselves do
not depend on it; this script only reads the finished result files.

    python scripts/make_figures.py        # writes figures/*.png
"""
import json
import os
import sys

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("matplotlib is needed only for the figures: pip install matplotlib")

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, "results")
OUT = os.path.join(ROOT, "figures")

BLUE = "#2a78d6"
ORANGE = "#eb6834"
INK = "#0b0b0b"
INK2 = "#52514e"
GRID = "#e6e5e1"
SURFACE = "#fcfcfb"

plt.rcParams.update({
    "font.family": "DejaVu Sans",
    "font.size": 10,
    "text.color": INK,
    "axes.labelcolor": INK2,
    "axes.edgecolor": GRID,
    "axes.facecolor": SURFACE,
    "figure.facecolor": SURFACE,
    "xtick.color": INK2,
    "ytick.color": INK2,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "axes.spines.left": False,
    "axes.titleweight": "bold",
    "axes.titlesize": 11,
    "axes.titlelocation": "left",
})


def load(name):
    with open(os.path.join(RES, name), encoding="utf-8") as f:
        return json.load(f)


def short(model):
    return model.split("/", 1)[1]


def dumbbell(ax, rows, a_label, b_label, title, xlabel):
    """rows: list of (name, a, b), drawn top to bottom in the given order."""
    n = len(rows)
    ys = list(range(n))[::-1]
    for y, (name, a, b) in zip(ys, rows):
        ax.plot([a, b], [y, y], color=GRID, lw=2, zorder=1)
        ax.plot(a, y, "o", color=INK2, ms=7, zorder=2, label=a_label if y == ys[0] else None)
        ax.plot(b, y, "o", color=BLUE, ms=7, zorder=3, label=b_label if y == ys[0] else None)
    ax.set_yticks(ys)
    ax.set_yticklabels([short(r[0]) for r in rows])
    ax.set_xlim(0, 0.8)
    ax.set_xticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_xticklabels(["0", "20", "40", "60", "80"])
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)
    ax.set_title(title, pad=10)
    ax.legend(frameon=False, loc="lower right", fontsize=9)


def fig_ranking():
    q1 = load("q1_q3_defects.json")["q1"]["per_model"]
    q4 = load("q4_repeats.json")["per_model"]
    order = sorted(q4, key=lambda m: -q4[m]["pass@1"])

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), sharey=False)
    dumbbell(
        ax1,
        [(m, q1[m]["raw"], q1[m]["clean"]) for m in order],
        "all 66 tasks", "30 defective tasks removed",
        "Removing known defective tasks (Q1)", "pass@1, percent of tasks solved",
    )
    dumbbell(
        ax2,
        [(m, q4[m]["pass@1"], q4[m]["pass^5"]) for m in order],
        "pass@1", "pass^5, solved in all 5 trials",
        "Ranking by reliability instead of success (Q4)", "percent of tasks",
    )
    ax2.set_yticklabels([])
    fig.suptitle(
        "The order of the ten Terminal-Bench 4.0 configurations barely moves under either correction",
        x=0.01, ha="left", fontsize=12, fontweight="bold",
    )
    fig.text(0.01, 0.01,
             "Configurations sorted by pass@1 on all tasks. 10 configurations x 66 tasks x 5 trials. "
             "No pair that swaps places does so beyond noise.",
             color=INK2, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.04, 1, 0.94))
    fig.savefig(os.path.join(OUT, "ranking_stability.png"), dpi=160)
    plt.close(fig)


def fig_power():
    pt = load("power_table.json")
    rows = pt["table"]
    tasks = [r["tasks"] for r in rows]
    tie1 = [r["pass1_tie_halfwidth_pp"] for r in rows]
    tie5 = [r["pass^5_tie_halfwidth_pp"] for r in rows]
    mdd = [r["pass1_mdd80_pp"] for r in rows]

    fig, ax = plt.subplots(figsize=(8, 4.6))
    ax.plot(tasks, mdd, color=ORANGE, lw=2, marker="o", ms=5, label="pass@1 difference detectable with 80% power")
    ax.plot(tasks, tie5, color=INK2, lw=2, marker="o", ms=5, label="pass^5 tie zone")
    ax.plot(tasks, tie1, color=BLUE, lw=2, marker="o", ms=5, label="pass@1 tie zone")
    ax.set_xscale("log")
    ax.set_xticks(tasks)
    ax.set_xticklabels([str(t) for t in tasks])
    ax.minorticks_off()
    ax.set_xlabel("tasks in the benchmark (5 trials each, log scale)")
    ax.set_ylabel("difference in percentage points")
    ax.set_ylim(0, 20)
    ax.grid(axis="y", color=GRID, lw=0.8)
    ax.set_axisbelow(True)
    ax.tick_params(axis="y", length=0)

    obs = pt["observed_tasks"]
    t66 = next(r for r in rows if r["tasks"] == obs)["pass1_tie_halfwidth_pp"]
    ax.axvline(obs, color=GRID, lw=1.2, ls="--", zorder=0)
    ax.annotate(f"Terminal-Bench 4.0: {obs} tasks,\nagents within {t66} points are tied",
                xy=(obs, t66), xytext=(140, 14.5), color=INK, fontsize=9,
                arrowprops=dict(arrowstyle="-", color=INK2, lw=0.8))
    ax.set_title("How many tasks a benchmark needs to tell two agents apart", pad=10)
    ax.legend(frameon=False, loc="lower left", fontsize=9)
    fig.text(0.01, 0.01,
             "Median over the 45 pairs of TB 4.0 configurations; standard error scaled as sqrt(66 / N),\n"
             "new tasks assumed to come from the same population.",
             color=INK2, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.07, 1, 1))
    fig.savefig(os.path.join(OUT, "tasks_needed.png"), dpi=160)
    plt.close(fig)


def fig_icc():
    tb40 = load("q5_icc_tb40.json")["main_mean_center"]
    tb20 = load("q5_icc_tb20.json")["main_mean_center"]

    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.6), sharey=True)
    for ax, d, name, n in ((ax1, tb40, "Terminal-Bench 4.0", "10 configurations"),
                           (ax2, tb20, "Terminal-Bench 2.0", "60 configurations")):
        xs = [d["pass1"][m] for m in d["icc"]]
        ys = [d["icc"][m] for m in d["icc"]]
        ax.scatter(xs, ys, s=46, color=BLUE, edgecolor=SURFACE, lw=1, zorder=3)
        ax.axhline(d["icc_center"], color=INK2, lw=1, ls="--", zorder=1)
        ax.text(0.01, d["icc_center"] + 0.012, f"mean ICC {d['icc_center']:.2f}",
                ha="left", va="bottom", color=INK2, fontsize=8.5, transform=ax.get_yaxis_transform())
        ax.set_title(f"{name}, {n}, p = {d['p']:.3g}", pad=10)
        ax.set_xlabel("pass@1, share of tasks solved")
        ax.set_xlim(0, 0.8)
        ax.grid(axis="y", color=GRID, lw=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis="y", length=0)
    ax1.set_ylabel("ICC, how correlated an agent's 5 repeats are")
    ax1.set_ylim(0, 1)
    fig.suptitle("Do agents differ in how correlated their repeats are? Not detectably on TB 4.0, yes on TB 2.0 (Q5)",
                 x=0.01, ha="left", fontsize=12, fontweight="bold")
    fig.text(0.01, 0.01,
             "p is the permutation test for whether the spread of ICC across configurations exceeds the spread under identical ICC.\n"
             "Much of the TB 2.0 difference sits in the 28 tasks later changed in TB 2.1.",
             color=INK2, fontsize=8.5)
    fig.tight_layout(rect=(0, 0.07, 1, 0.94))
    fig.savefig(os.path.join(OUT, "icc_heterogeneity.png"), dpi=160)
    plt.close(fig)


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    fig_ranking()
    fig_power()
    fig_icc()
    print("wrote", OUT)
