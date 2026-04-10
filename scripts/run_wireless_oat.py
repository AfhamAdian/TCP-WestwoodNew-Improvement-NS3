#!/usr/bin/env python3

import argparse
import csv
import itertools
import subprocess
import sys
from pathlib import Path

VARIANTS = [
    "TcpDualModifiedTcpWestwoodPlusNew",
    "TcpWestwoodPlusNew",
    "TcpWestwoodPlus",
]

BASELINE = {"nNodes": 60, "nFlows": 30, "packetsPerSecond": 300}
NODES = [20, 40, 60, 80, 100]
FLOWS = [10, 20, 30, 40, 50]
PPS = [100, 200, 300, 400, 500]
COVERAGE = [1, 2, 3, 4, 5]


def build_oat_configs():
    configs = set()
    for n in NODES:
        configs.add((n, BASELINE["nFlows"], BASELINE["packetsPerSecond"], 2))
    for f in FLOWS:
        configs.add((BASELINE["nNodes"], f, BASELINE["packetsPerSecond"], 2))
    for p in PPS:
        configs.add((BASELINE["nNodes"], BASELINE["nFlows"], p, 2))
    for c in COVERAGE:
        configs.add((BASELINE["nNodes"], BASELINE["nFlows"], BASELINE["packetsPerSecond"], c))

    return [
        {"nNodes": n, "nFlows": f, "packetsPerSecond": p, "coverageMultiplier": c}
        for (n, f, p, c) in sorted(configs, key=lambda x: (x[0], x[1], x[2], x[3]))
    ]


def build_sanity_config():
    return [{"nNodes": 20, "nFlows": 10, "packetsPerSecond": 100, "coverageMultiplier": 2}]


def run_one(ns3_path: Path, cfg, variant, args):
    sim_args = (
        f"wireless-static-sim "
        f"--tcpVariant={variant} "
        f"--nNodes={cfg['nNodes']} "
        f"--nFlows={cfg['nFlows']} "
        f"--packetsPerSecond={cfg['packetsPerSecond']} "
        f"--coverageMultiplier={cfg['coverageMultiplier']} "
        f"--simulationTime={args.simulation_time}"
    )

    cmd = [str(ns3_path), "run", sim_args]
    proc = subprocess.run(cmd, capture_output=True, text=True, check=False)
    if proc.returncode != 0:
        return proc.returncode, ""

    line = ""
    for candidate in reversed(proc.stdout.strip().splitlines()):
        if candidate.count(",") >= 9:
            line = candidate.strip()
            break

    return 0, line


def write_manifest(output_path: Path, rows):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "runTag",
                "nNodes",
                "nFlows",
                "packetsPerSecond",
                "coverageMultiplier",
                "variant",
                "simulationTime",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Run wireless static OAT simulations")
    parser.add_argument("--mode", choices=["sanity", "full-oat"], required=True)
    parser.add_argument("--run-tag", required=True)
    parser.add_argument("--simulation-time", type=float, default=20.0)
    parser.add_argument("--ns3", default="./ns3")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ns3_path = Path(args.ns3).resolve()
    if not ns3_path.exists():
        print(f"ns3 wrapper not found: {ns3_path}")
        return 1

    configs = build_sanity_config() if args.mode == "sanity" else build_oat_configs()

    plan_rows = []
    for cfg, variant in itertools.product(configs, VARIANTS):
        plan_rows.append(
            {
                "runTag": args.run_tag,
                "nNodes": cfg["nNodes"],
                "nFlows": cfg["nFlows"],
                "packetsPerSecond": cfg["packetsPerSecond"],
                "coverageMultiplier": cfg["coverageMultiplier"],
                "variant": variant,
                "simulationTime": args.simulation_time,
            }
        )

    base_dir = Path("data") / "wireless_oat" / args.run_tag
    manifest_path = base_dir / "manifest.csv"
    summary_path = base_dir / "summary.csv"

    write_manifest(manifest_path, plan_rows)

    print(f"Mode: {args.mode}")
    print(f"Configs: {len(configs)}")
    print(f"Total runs (configs x variants): {len(plan_rows)}")
    print(f"Manifest: {manifest_path}")

    if args.dry_run:
        return 0

    base_dir.mkdir(parents=True, exist_ok=True)
    with summary_path.open("w", newline="") as f:
        f.write(
            "tcpVariant,nNodes,nFlows,packetsPerSecond,coverageMultiplier,"
            "throughput_kbps,avgDelay_ms,pdr_percent,dropRatio_percent,energy_joules\n"
        )

        failures = 0
        for index, row in enumerate(plan_rows, start=1):
            cfg = {
                "nNodes": row["nNodes"],
                "nFlows": row["nFlows"],
                "packetsPerSecond": row["packetsPerSecond"],
                "coverageMultiplier": row["coverageMultiplier"],
            }
            variant = row["variant"]
            print(
                f"[{index}/{len(plan_rows)}] n={cfg['nNodes']} f={cfg['nFlows']} "
                f"pps={cfg['packetsPerSecond']} cov={cfg['coverageMultiplier']} variant={variant}"
            )
            code, line = run_one(ns3_path, cfg, variant, args)
            if code != 0 or not line:
                failures += 1
                print("Run failed or no CSV line returned")
                continue
            f.write(line + "\n")

    if failures:
        print(f"Completed with failures: {failures}")
        return 2

    print("All runs completed successfully")
    print(f"Summary: {summary_path}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
