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

BASELINE = {"nNodes": 60, "nFlows": 30, "pps": 300}
NODES = [20, 40, 60, 80, 100]
FLOWS = [10, 20, 30, 40, 50]
PPS = [100, 200, 300, 400, 500]


def build_oat_configs():
    configs = set()

    for n in NODES:
        configs.add((n, BASELINE["nFlows"], BASELINE["pps"]))
    for f in FLOWS:
        configs.add((BASELINE["nNodes"], f, BASELINE["pps"]))
    for p in PPS:
        configs.add((BASELINE["nNodes"], BASELINE["nFlows"], p))

    return [
        {"nNodes": n, "nFlows": f, "pps": p}
        for (n, f, p) in sorted(configs, key=lambda x: (x[0], x[1], x[2]))
    ]


def build_sanity_config():
    return [{"nNodes": 20, "nFlows": 10, "pps": 100}]


def run_one(ns3_path: Path, cfg, variant, args):
    sim_args = (
        f"scratch/tcp-westwood-wired-dumbbell "
        f"--nNodes={cfg['nNodes']} "
        f"--nFlows={cfg['nFlows']} "
        f"--pps={cfg['pps']} "
        f"--simulationTime={args.simulation_time} "
        f"--samplingInterval={args.sampling_interval} "
        f"--seed={args.seed} "
        f"--runTag={args.run_tag} "
        f"--enableCwnd={'true' if args.enable_cwnd else 'false'} "
        f"--verbose={'true' if args.verbose else 'false'} "
        f"--variant={variant}"
    )

    cmd = [str(ns3_path), "run", sim_args]
    print(" ".join(cmd))
    return subprocess.run(cmd, check=False)


def write_manifest(output_path: Path, rows):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=["runTag", "nNodes", "nFlows", "pps", "variant", "seed", "simulationTime", "samplingInterval"],
        )
        writer.writeheader()
        writer.writerows(rows)


def main():
    parser = argparse.ArgumentParser(description="Run wired OAT simulations for Westwood variants")
    parser.add_argument("--mode", choices=["sanity", "full-oat"], required=True)
    parser.add_argument("--run-tag", required=True, help="Folder name under data/wired_oat/")
    parser.add_argument("--simulation-time", type=float, default=20.0)
    parser.add_argument("--sampling-interval", type=float, default=5.0)
    parser.add_argument("--seed", type=int, default=1)
    parser.add_argument("--enable-cwnd", action="store_true", help="Enable cwnd tracing")
    parser.add_argument("--verbose", action="store_true")
    parser.add_argument("--ns3", default="./ns3", help="Path to ns3 wrapper")
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()

    ns3_path = Path(args.ns3).resolve()
    if not ns3_path.exists():
        print(f"ns3 wrapper not found: {ns3_path}")
        return 1

    if args.mode == "sanity":
        configs = build_sanity_config()
    else:
        configs = build_oat_configs()

    plan_rows = []
    for cfg, variant in itertools.product(configs, VARIANTS):
        plan_rows.append(
            {
                "runTag": args.run_tag,
                "nNodes": cfg["nNodes"],
                "nFlows": cfg["nFlows"],
                "pps": cfg["pps"],
                "variant": variant,
                "seed": args.seed,
                "simulationTime": args.simulation_time,
                "samplingInterval": args.sampling_interval,
            }
        )

    manifest_path = Path("data") / "wired_oat" / args.run_tag / "manifest.csv"
    write_manifest(manifest_path, plan_rows)

    print(f"Mode: {args.mode}")
    print(f"Configs: {len(configs)}")
    print(f"Total runs (configs x variants): {len(plan_rows)}")
    print(f"Manifest: {manifest_path}")

    if args.dry_run:
        return 0

    failures = 0
    for index, row in enumerate(plan_rows, start=1):
        cfg = {"nNodes": row["nNodes"], "nFlows": row["nFlows"], "pps": row["pps"]}
        variant = row["variant"]
        print(f"[{index}/{len(plan_rows)}] n={cfg['nNodes']} f={cfg['nFlows']} p={cfg['pps']} variant={variant}")
        proc = run_one(ns3_path, cfg, variant, args)
        if proc.returncode != 0:
            failures += 1
            print(f"Run failed with code {proc.returncode}")

    if failures:
        print(f"Completed with failures: {failures}")
        return 2

    print("All runs completed successfully")
    return 0


if __name__ == "__main__":
    sys.exit(main())
