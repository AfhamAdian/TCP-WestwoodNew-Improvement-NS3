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

METRICS = {
    "avgThroughputMbps": "Average Throughput (Mbps)",
    "avgDelaySec": "Average End-to-End Delay (s)",
    "pdr": "Packet Delivery Ratio",
    "dropRatio": "Packet Drop Ratio",
}


def read_summary(summary_path: Path):
    rows = []
    with summary_path.open() as f:
        reader = csv.DictReader(f)
        for row in reader:
            rows.append(
                {
                    "runTag": row["runTag"],
                    "variant": row["variant"],
                    "nNodes": int(row["nNodes"]),
                    "nFlows": int(row["nFlows"]),
                    "pps": int(row["pps"]),
                    "seed": int(row["seed"]),
                    "simulationTime": float(row["simulationTime"]),
                    "avgThroughputMbps": float(row["avgThroughputMbps"]),
                    "avgDelaySec": float(row["avgDelaySec"]),
                    "pdr": float(row["pdr"]),
                    "dropRatio": float(row["dropRatio"]),
                }
            )
    return rows


def plot_sanity_timeseries(run_root: Path, plot_dir: Path):
    config_dirs = sorted([p for p in run_root.iterdir() if p.is_dir() and p.name.startswith("n")])
    if not config_dirs:
        print("No config folders found for sanity plots")
        return

    config_dir = config_dirs[0]
    metric_files = {
        "throughput": ("throughput.dat", "Throughput (Kbps)"),
        "delay": ("delay.dat", "Delay (s)"),
        "pdr": ("pdr.dat", "PDR"),
        "drop_ratio": ("drop_ratio.dat", "Drop Ratio"),
        "cwnd": ("cwnd.dat", "Congestion Window (bytes)"),
    }

    for metric_key, (filename, ylabel) in metric_files.items():
        fig, ax = plt.subplots(figsize=(10, 5))
        for variant in VARIANTS:
            data_file = config_dir / variant / filename
            if not data_file.exists():
                continue
            t_vals, y_vals = [], []
            with data_file.open() as f:
                for line in f:
                    line = line.strip()
                    if not line or line.startswith("#"):
                        continue
                    parts = line.split("\t")
                    if len(parts) < 2:
                        continue
                    t_vals.append(float(parts[0]))
                    y_vals.append(float(parts[1]))
            if t_vals:
                if metric_key == "cwnd":
                    ax.plot(t_vals, y_vals, linestyle="-", linewidth=1.8, label=variant)
                else:
                    ax.plot(t_vals, y_vals, marker="o", linewidth=1.6, label=variant)

        ax.set_title(f"Sanity Time Series: {metric_key}")
        ax.set_xlabel("Time (s)")
        ax.set_ylabel(ylabel)
        ax.grid(alpha=0.3)
        ax.legend()
        fig.tight_layout()
        out = plot_dir / f"sanity_{metric_key}.png"
        fig.savefig(out, dpi=220)
        plt.close(fig)
        print(f"Saved {out}")


def plot_oat_sweeps(rows, plot_dir: Path):
    baseline = {"nNodes": 60, "nFlows": 30, "pps": 300}

    sweeps = {
        "nodes": {
            "x_key": "nNodes",
            "x_vals": [20, 40, 60, 80, 100],
            "fixed": {"nFlows": baseline["nFlows"], "pps": baseline["pps"]},
            "xlabel": "Number of Nodes",
        },
        "flows": {
            "x_key": "nFlows",
            "x_vals": [10, 20, 30, 40, 50],
            "fixed": {"nNodes": baseline["nNodes"], "pps": baseline["pps"]},
            "xlabel": "Number of Flows",
        },
        "pps": {
            "x_key": "pps",
            "x_vals": [100, 200, 300, 400, 500],
            "fixed": {"nNodes": baseline["nNodes"], "nFlows": baseline["nFlows"]},
            "xlabel": "Packets per Second",
        },
    }

    for sweep_name, sweep in sweeps.items():
        for metric_key, metric_label in METRICS.items():
            fig, ax = plt.subplots(figsize=(10, 5))
            for variant in VARIANTS:
                points = []
                for x in sweep["x_vals"]:
                    candidates = []
                    for row in rows:
                        if row["variant"] != variant:
                            continue
                        if row[sweep["x_key"]] != x:
                            continue
                        fixed_ok = True
                        for k, v in sweep["fixed"].items():
                            if row[k] != v:
                                fixed_ok = False
                                break
                        if fixed_ok:
                            candidates.append(row)
                    if candidates:
                        points.append((x, sum(c[metric_key] for c in candidates) / len(candidates)))

                if points:
                    xs, ys = zip(*points)
                    ax.plot(xs, ys, marker="o", linewidth=1.8, label=variant)

            ax.set_title(f"OAT Sweep ({sweep_name}) - {metric_label}")
            ax.set_xlabel(sweep["xlabel"])
            ax.set_ylabel(metric_label)
            ax.grid(alpha=0.3)
            ax.legend()
            fig.tight_layout()
            out = plot_dir / f"oat_{sweep_name}_{metric_key}.png"
            fig.savefig(out, dpi=220)
            plt.close(fig)
            print(f"Saved {out}")


def plot_requested_parameter_graphs(rows, plot_dir: Path):
    baseline = {"nNodes": 60, "nFlows": 30, "pps": 300}

    requested = [
        ("nNodes", [20, 40, 60, 80, 100], {"nFlows": baseline["nFlows"], "pps": baseline["pps"]}, "Nodes"),
        ("nFlows", [10, 20, 30, 40, 50], {"nNodes": baseline["nNodes"], "pps": baseline["pps"]}, "Flows"),
        ("pps", [100, 200, 300, 400, 500], {"nNodes": baseline["nNodes"], "nFlows": baseline["nFlows"]}, "Packet Rate"),
    ]

    metric_targets = [
        ("avgThroughputMbps", "Throughput"),
        ("avgDelaySec", "Delay"),
        ("pdr", "PDR"),
        ("dropRatio", "Drop Ratio"),
    ]

    ylabels = {
        "avgThroughputMbps": "Throughput (Mbps)",
        "avgDelaySec": "Delay (s)",
        "pdr": "PDR",
        "dropRatio": "Drop Ratio",
    }

    for x_key, x_vals, fixed, x_label in requested:
        for metric_key, metric_name in metric_targets:
            fig, ax = plt.subplots(figsize=(10, 5))

            for variant in VARIANTS:
                points = []
                for x in x_vals:
                    candidates = []
                    for row in rows:
                        if row["variant"] != variant:
                            continue
                        if row[x_key] != x:
                            continue
                        fixed_ok = True
                        for k, v in fixed.items():
                            if row[k] != v:
                                fixed_ok = False
                                break
                        if fixed_ok:
                            candidates.append(row)

                    if candidates:
                        points.append((x, sum(c[metric_key] for c in candidates) / len(candidates)))

                if points:
                    xs, ys = zip(*points)
                    ax.plot(xs, ys, linestyle="-", linewidth=1.9, label=variant)

            ax.set_title(f"{metric_name} vs {x_label}")
            ax.set_xlabel(x_label)
            ax.set_ylabel(ylabels[metric_key])
            ax.grid(alpha=0.3)
            ax.legend()
            fig.tight_layout()

            safe_x = x_label.lower().replace(" ", "_")
            safe_m = metric_name.lower().replace(" ", "_")
            out = plot_dir / f"{safe_m}_vs_{safe_x}.png"
            fig.savefig(out, dpi=220)
            plt.close(fig)
            print(f"Saved {out}")


def main():
    parser = argparse.ArgumentParser(description="Plot wired OAT outputs")
    parser.add_argument("--run-tag", required=True)
    parser.add_argument("--mode", choices=["sanity", "full-oat", "requested"], required=True)
    args = parser.parse_args()

    run_root = Path("data") / "wired_oat" / args.run_tag
    summary_path = run_root / "summary.csv"
    if not summary_path.exists():
        print(f"summary.csv not found: {summary_path}")
        return 1

    rows = read_summary(summary_path)
    if args.mode == "sanity":
        plot_dir = Path("plots") / "wired_oat" / args.run_tag
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_sanity_timeseries(run_root, plot_dir)
        print(f"Plots written to {plot_dir}")
    elif args.mode == "full-oat":
        plot_dir = Path("plots") / "wired_oat" / args.run_tag
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_oat_sweeps(rows, plot_dir)
        print(f"Plots written to {plot_dir}")
    else:
        plot_dir = Path("plots") / "wired_oat_requested" / args.run_tag
        plot_dir.mkdir(parents=True, exist_ok=True)
        plot_requested_parameter_graphs(rows, plot_dir)
        print(f"Requested plots written to {plot_dir}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
