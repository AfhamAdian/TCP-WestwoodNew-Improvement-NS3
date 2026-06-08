#!/usr/bin/env python3
"""
plot_wireless_static.py — Generate comparison plots for wireless static simulations.

Reads:  results_wireless_static/summary.csv
Writes: plots_wireless_static/*.png  (20 plots: 4 sweeps × 5 metrics)
"""

import os
import sys
import csv
import matplotlib.pyplot as plt

CSV_FILE  = "results_wireless_static/summary.csv"
PLOT_DIR  = "plots_wireless_static"

# ── Metrics ──
METRICS = [
    ("throughput_kbps",      "Network Throughput (Kbps)"),
    ("avgDelay_ms",          "End-to-End Delay (ms)"),
    ("pdr_percent",          "Packet Delivery Ratio (%)"),
    ("dropRatio_percent",    "Packet Drop Ratio (%)"),
    ("energy_joules",        "Energy Consumption (Joules)"),
]

# ── Parameter sweeps ──
SWEEPS = [
    {
        "param_col":   "nNodes",
        "label":       "Number of Nodes",
        "fixed":       {"nFlows": 20, "packetsPerSecond": 200, "coverageMultiplier": 2},
    },
    {
        "param_col":   "nFlows",
        "label":       "Number of Flows",
        "fixed":       {"nNodes": 40, "packetsPerSecond": 200, "coverageMultiplier": 2},
    },
    {
        "param_col":   "packetsPerSecond",
        "label":       "Packets per Second",
        "fixed":       {"nNodes": 40, "nFlows": 20, "coverageMultiplier": 2},
    },
    {
        "param_col":   "coverageMultiplier",
        "label":       "Coverage Area (×Tx_range)",
        "fixed":       {"nNodes": 40, "nFlows": 20, "packetsPerSecond": 200},
    },
]

# ── Colors per variant ──
COLORS = {
    "TcpDualModifiedTcpWestwoodPlusNew": "#1f77b4",
    "TcpWestwoodPlusNew":                "#d62728",
    "TcpWestwoodPlus":                   "#2ca02c",
}
MARKERS = {
    "TcpDualModifiedTcpWestwoodPlusNew": "o",
    "TcpWestwoodPlusNew":                "s",
    "TcpWestwoodPlus":                   "^",
}


def load_data():
    if not os.path.exists(CSV_FILE):
        print(f"ERROR: {CSV_FILE} not found. Run the simulation first.")
        sys.exit(1)
    rows = []
    with open(CSV_FILE, newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "tcpVariant": row["tcpVariant"],
                    "nNodes": int(row["nNodes"]),
                    "nFlows": int(row["nFlows"]),
                    "packetsPerSecond": int(row["packetsPerSecond"]),
                    "coverageMultiplier": int(row["coverageMultiplier"]),
                    "throughput_kbps": float(row["throughput_kbps"]),
                    "avgDelay_ms": float(row["avgDelay_ms"]),
                    "pdr_percent": float(row["pdr_percent"]),
                    "dropRatio_percent": float(row["dropRatio_percent"]),
                    "energy_joules": float(row["energy_joules"]),
                }
            )
    variants = sorted({r["tcpVariant"] for r in rows})
    print(f"Loaded {len(rows)} rows from {CSV_FILE}")
    print(f"Variants found: {variants}")
    return rows


def filter_sweep(df, sweep):
    """Return rows matching this sweep's fixed parameters."""
    out = []
    for row in df:
        ok = True
        for col, val in sweep["fixed"].items():
            if row[col] != val:
                ok = False
                break
        if ok:
            out.append(row)
    return out


def plot_metric(df, sweep, metric_col, metric_label, ax):
    """Plot one metric for one sweep on the given axes."""
    param_col  = sweep["param_col"]
    param_label = sweep["label"]

    variants = sorted({row["tcpVariant"] for row in df})
    for variant in variants:
        sub = sorted([row for row in df if row["tcpVariant"] == variant], key=lambda r: r[param_col])
        if not sub:
            continue
        color  = COLORS.get(variant, "#333333")
        marker = MARKERS.get(variant, "o")
        # Use a shorter label for the legend
        short = variant.replace("Tcp", "")
        xs = [row[param_col] for row in sub]
        ys = [row[metric_col] for row in sub]
        ax.plot(xs, ys,
                color=color, marker=marker, linewidth=2, markersize=7,
                label=short, alpha=0.9)

    ax.set_xlabel(param_label, fontsize=12)
    ax.set_ylabel(metric_label, fontsize=12)
    ax.set_title(f"{metric_label}  vs  {param_label}", fontsize=13, fontweight="bold")
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)


def main():
    os.makedirs(PLOT_DIR, exist_ok=True)
    df = load_data()

    count = 0
    for sweep in SWEEPS:
        sweep_df = filter_sweep(df, sweep)
        if sweep_df.empty:
            print(f"  [skip] No data for sweep: {sweep['label']}")
            continue

        for metric_col, metric_label in METRICS:
            fig, ax = plt.subplots(figsize=(10, 6))
            plot_metric(sweep_df, sweep, metric_col, metric_label, ax)
            fig.tight_layout()

            fname = f"{sweep['param_col']}_vs_{metric_col}.png"
            path  = os.path.join(PLOT_DIR, fname)
            fig.savefig(path, dpi=200)
            plt.close(fig)
            count += 1

    print(f"\n✓ Generated {count} plots in {PLOT_DIR}/")

    # ── Also create a combined summary figure per sweep ──
    for sweep in SWEEPS:
        sweep_df = filter_sweep(df, sweep)
        if sweep_df.empty:
            continue

        fig, axes = plt.subplots(2, 3, figsize=(20, 11))
        fig.suptitle(f"Wireless Static — Varying {sweep['label']}",
                     fontsize=16, fontweight="bold")

        for idx, (metric_col, metric_label) in enumerate(METRICS):
            row, col = divmod(idx, 3)
            plot_metric(sweep_df, sweep, metric_col, metric_label, axes[row][col])

        # Hide the 6th subplot (2×3 with 5 metrics)
        axes[1][2].set_visible(False)

        fig.tight_layout(rect=[0, 0, 1, 0.95])
        fname = f"summary_{sweep['param_col']}.png"
        fig.savefig(os.path.join(PLOT_DIR, fname), dpi=200)
        plt.close(fig)

    print(f"✓ Generated summary figures in {PLOT_DIR}/")


if __name__ == "__main__":
    main()
