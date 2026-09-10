#!/usr/bin/env python3
"""Generate benchmark_chart.png from results/results.json.

Renders one horizontal bar panel per mode (default, fsync, large), each
ranking providers by mean total time (fastest on top). Run after updating
results.json with new provider numbers.

Usage:
  python generate_chart.py            # -> benchmark_chart.png
  python generate_chart.py --out x.png
"""
import argparse
import json
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).parent
RESULTS = ROOT / "results" / "results.json"

# Stable per-provider colors; Tenki highlighted.
COLORS = {
    "tenki": "#e8590c",
    "tensorlake": "#1c7ed6",
    "vercel": "#495057",
    "e2b": "#37b24d",
    "modal": "#ae3ec9",
    "daytona": "#f08c00",
}
DEFAULT_COLOR = "#868e96"

MODE_ORDER = ["default", "fsync", "large"]


def load():
    with open(RESULTS) as f:
        return json.load(f)


def panel(ax, mode_key, mode_data):
    providers = [p for p in mode_data if p != "description"]
    ranked = sorted(providers, key=lambda p: mode_data[p]["total_mean"])
    # Fastest on top: reverse for barh (which plots bottom-up).
    ranked = ranked[::-1]

    labels = [p.capitalize() for p in ranked]
    values = [mode_data[p]["total_mean"] for p in ranked]
    errs = [mode_data[p].get("total_stddev", 0) for p in ranked]
    colors = [COLORS.get(p, DEFAULT_COLOR) for p in ranked]

    y = range(len(ranked))
    ax.barh(y, values, xerr=errs, color=colors, height=0.62,
            error_kw={"ecolor": "#adb5bd", "capsize": 3, "elinewidth": 1})
    ax.set_yticks(list(y))
    ax.set_yticklabels(labels, fontsize=10)
    ax.set_xlabel("Total time (s) — lower is better", fontsize=9)
    ax.set_title(mode_data.get("description", mode_key), fontsize=10, pad=8)
    ax.grid(axis="x", color="#e9ecef", linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for spine in ("top", "right"):
        ax.spines[spine].set_visible(False)

    xmax = max(v + e for v, e in zip(values, errs))
    ax.set_xlim(0, xmax * 1.18)
    for yi, (v, e) in enumerate(zip(values, errs)):
        ax.text(v + e + xmax * 0.015, yi, f"{v:.2f}s",
                va="center", fontsize=9, color="#212529")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "benchmark_chart.png"))
    args = ap.parse_args()

    data = load()
    results = data["results"]
    modes = [m for m in MODE_ORDER if m in results]

    fig, axes = plt.subplots(len(modes), 1, figsize=(9, 4.2 * len(modes)))
    if len(modes) == 1:
        axes = [axes]

    n_providers = len({p for m in modes for p in results[m] if p != "description"})
    fig.suptitle("SQLite Performance Across Sandbox Providers",
                 fontsize=15, fontweight="bold", y=0.995)
    fig.text(0.5, 0.965,
             f"{n_providers} providers · 2 vCPU / 4 GB · "
             f"{data['config']['iterations']} iterations (mean ± stddev)",
             ha="center", fontsize=10, color="#495057")

    for ax, mode in zip(axes, modes):
        panel(ax, mode, results[mode])

    fig.tight_layout(rect=[0, 0, 1, 0.95])
    fig.subplots_adjust(hspace=0.32)
    fig.savefig(args.out, dpi=150, bbox_inches="tight", facecolor="white")
    print(f"Wrote {args.out}")


if __name__ == "__main__":
    main()
