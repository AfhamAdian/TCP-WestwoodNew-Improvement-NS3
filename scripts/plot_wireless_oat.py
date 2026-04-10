#!/usr/bin/env python3

import argparse
import csv
from pathlib import Path

import matplotlib.pyplot as plt

VARIANTS = [
    "TcpDualModifiedTcpWestwoodPlusNew",
    "TcpWestwoodPlusNew",
    "TcpWestwoodPlus",
]

PLOT_SPECS = [
    ("nNodes", [20, 40, 60, 80, 100], {"nFlows": 30, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Nodes", "throughput_kbps", "Throughput", "Throughput (Kbps)", "throughput_vs_nodes.png"),
    ("nNodes", [20, 40, 60, 80, 100], {"nFlows": 30, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Nodes", "avgDelay_ms", "Delay", "Delay (ms)", "delay_vs_nodes.png"),
    ("nNodes", [20, 40, 60, 80, 100], {"nFlows": 30, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Nodes", "pdr_percent", "PDR", "PDR (%)", "pdr_vs_nodes.png"),
    ("nNodes", [20, 40, 60, 80, 100], {"nFlows": 30, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Nodes", "dropRatio_percent", "Drop Ratio", "Drop Ratio (%)", "drop_ratio_vs_nodes.png"),
    ("nFlows", [10, 20, 30, 40, 50], {"nNodes": 60, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Flows", "throughput_kbps", "Throughput", "Throughput (Kbps)", "throughput_vs_flows.png"),
    ("nFlows", [10, 20, 30, 40, 50], {"nNodes": 60, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Flows", "avgDelay_ms", "Delay", "Delay (ms)", "delay_vs_flows.png"),
    ("nFlows", [10, 20, 30, 40, 50], {"nNodes": 60, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Flows", "pdr_percent", "PDR", "PDR (%)", "pdr_vs_flows.png"),
    ("nFlows", [10, 20, 30, 40, 50], {"nNodes": 60, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Flows", "dropRatio_percent", "Drop Ratio", "Drop Ratio (%)", "drop_ratio_vs_flows.png"),
    ("packetsPerSecond", [100, 200, 300, 400, 500], {"nNodes": 60, "nFlows": 30, "coverageMultiplier": 2}, "Packet Rate", "throughput_kbps", "Throughput", "Throughput (Kbps)", "throughput_vs_packet_rate.png"),
    ("packetsPerSecond", [100, 200, 300, 400, 500], {"nNodes": 60, "nFlows": 30, "coverageMultiplier": 2}, "Packet Rate", "avgDelay_ms", "Delay", "Delay (ms)", "delay_vs_packet_rate.png"),
    ("packetsPerSecond", [100, 200, 300, 400, 500], {"nNodes": 60, "nFlows": 30, "coverageMultiplier": 2}, "Packet Rate", "pdr_percent", "PDR", "PDR (%)", "pdr_vs_packet_rate.png"),
    ("packetsPerSecond", [100, 200, 300, 400, 500], {"nNodes": 60, "nFlows": 30, "coverageMultiplier": 2}, "Packet Rate", "dropRatio_percent", "Drop Ratio", "Drop Ratio (%)", "drop_ratio_vs_packet_rate.png"),
    ("coverageMultiplier", [1, 2, 3, 4, 5], {"nNodes": 60, "nFlows": 30, "packetsPerSecond": 300}, "Coverage Area (xTx_range)", "throughput_kbps", "Throughput", "Throughput (Kbps)", "throughput_vs_coverage.png"),
    ("coverageMultiplier", [1, 2, 3, 4, 5], {"nNodes": 60, "nFlows": 30, "packetsPerSecond": 300}, "Coverage Area (xTx_range)", "avgDelay_ms", "Delay", "Delay (ms)", "delay_vs_coverage.png"),
    ("coverageMultiplier", [1, 2, 3, 4, 5], {"nNodes": 60, "nFlows": 30, "packetsPerSecond": 300}, "Coverage Area (xTx_range)", "pdr_percent", "PDR", "PDR (%)", "pdr_vs_coverage.png"),
    ("coverageMultiplier", [1, 2, 3, 4, 5], {"nNodes": 60, "nFlows": 30, "packetsPerSecond": 300}, "Coverage Area (xTx_range)", "dropRatio_percent", "Drop Ratio", "Drop Ratio (%)", "drop_ratio_vs_coverage.png"),
    ("coverageMultiplier", [1, 2, 3, 4, 5], {"nNodes": 60, "nFlows": 30, "packetsPerSecond": 300}, "Coverage Area (xTx_range)", "energy_joules", "Energy Consumption", "Energy (J)", "energy_vs_coverage.png"),
    ("nNodes", [20, 40, 60, 80, 100], {"nFlows": 30, "packetsPerSecond": 300, "coverageMultiplier": 2}, "Nodes", "energy_joules", "Energy Consumption", "Energy (J)", "energy_vs_nodes.png"),
]


def read_summary(summary_path: Path):
    rows = []
    with summary_path.open(newline="") as f:
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
    return rows


def filter_rows(rows, x_key, x_val, fixed):
    out = []
    for row in rows:
        if row[x_key] != x_val:
            continue
        ok = True
        for k, v in fixed.items():
            if row[k] != v:
                ok = False
                break
        if ok:
            out.append(row)
    return out


def main():
    parser = argparse.ArgumentParser(description="Plot wireless OAT requested graphs")
    parser.add_argument("--run-tag", required=True)
    args = parser.parse_args()

    summary = Path("data") / "wireless_oat" / args.run_tag / "summary.csv"
    if not summary.exists():
        print(f"summary.csv not found: {summary}")
        return 1

    rows = read_summary(summary)
    out_dir = Path("plots") / "wireless_oat_requested" / args.run_tag
    out_dir.mkdir(parents=True, exist_ok=True)

    for x_key, x_vals, fixed, x_label, y_key, title_left, y_label, out_name in PLOT_SPECS:
        fig, ax = plt.subplots(figsize=(10, 5))
        has_series = False

        for variant in VARIANTS:
            points = []
            for x in x_vals:
                candidates = [r for r in filter_rows(rows, x_key, x, fixed) if r["tcpVariant"] == variant]
                if candidates:
                    points.append((x, sum(c[y_key] for c in candidates) / len(candidates)))
            if points:
                xs, ys = zip(*points)
                ax.plot(xs, ys, linestyle="-", linewidth=1.9, label=variant)
                has_series = True

        ax.set_title(f"{title_left} vs {x_label}")
        ax.set_xlabel(x_label)
        ax.set_ylabel(y_label)
        ax.grid(alpha=0.3)
        if has_series:
            ax.legend()
        fig.tight_layout()
        out_file = out_dir / out_name
        fig.savefig(out_file, dpi=220)
        plt.close(fig)
        print(f"Saved {out_file}")

    print(f"Plots written to {out_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
