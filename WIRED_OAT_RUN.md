# Wired OAT Simulation Run Guide

This guide explains how to run the wired dumbbell TCP experiments for:

- `TcpDualModifiedTcpWestwoodPlusNew`
- `TcpWestwoodPlusNew`
- `TcpWestwoodPlus`

using the scripts added in this workspace.

---

## 1) What is included

- Simulator: `scratch/tcp-westwood-wired-dumbbell.cc`
- Automation runner: `scripts/run_wired_oat.py`
- Plotting script: `scripts/plot_wired_oat.py`

Topology used: **wired dumbbell with one bottleneck link**.

---

## 2) One-time note (already done in this workspace)

To avoid unrelated build failures, `scratch/wireless-static-sim.cc` is excluded from scratch auto-build in `scratch/CMakeLists.txt`.

---

## 3) Sanity run (recommended first)

Runs one configuration across all 3 variants:

- nodes = 20
- flows = 10
- pps = 100
- simulation time = 20s

### Command

```bash
python3 scripts/run_wired_oat.py \
  --mode sanity \
  --run-tag wired_sanity \
  --simulation-time 20 \
  --sampling-interval 2 \
  --enable-cwnd
```

### Generate sanity plots

```bash
python3 scripts/plot_wired_oat.py --run-tag wired_sanity --mode sanity
```

### Expected sanity plots

- `plots/wired_oat/wired_sanity/sanity_throughput.png`
- `plots/wired_oat/wired_sanity/sanity_delay.png`
- `plots/wired_oat/wired_sanity/sanity_pdr.png`
- `plots/wired_oat/wired_sanity/sanity_drop_ratio.png`
- `plots/wired_oat/wired_sanity/sanity_cwnd.png`

---

## 4) Full wired OAT run

OAT = one-factor-at-a-time with baseline `(nNodes=60, nFlows=30, pps=300)`.

Unique configs = **13**.
With 3 variants, total runs = **39**.

### Command

```bash
python3 scripts/run_wired_oat.py \
  --mode full-oat \
  --run-tag wired_oat_full \
  --simulation-time 20 \
  --sampling-interval 5
```

### Generate OAT sweep plots

```bash
python3 scripts/plot_wired_oat.py --run-tag wired_oat_full --mode full-oat
```

---

## 5) Output structure

For each run tag:

- `data/wired_oat/<run-tag>/manifest.csv` (planned runs)
- `data/wired_oat/<run-tag>/summary.csv` (final metrics per run)
- `data/wired_oat/<run-tag>/<config>/<variant>/throughput.dat`
- `data/wired_oat/<run-tag>/<config>/<variant>/delay.dat`
- `data/wired_oat/<run-tag>/<config>/<variant>/pdr.dat`
- `data/wired_oat/<run-tag>/<config>/<variant>/drop_ratio.dat`
- `data/wired_oat/<run-tag>/<config>/<variant>/cwnd.dat` (when `--enable-cwnd` is used)

Plots are written to:

- `plots/wired_oat/<run-tag>/`

---

## 6) Metrics in summary.csv

`summary.csv` columns:

- `avgThroughputMbps`
- `avgDelaySec`
- `pdr`
- `dropRatio`
- plus packet counters (`txPackets`, `rxPackets`, `lostPackets`)

---

## 7) Useful options

### Dry run (plan only, no simulation execution)

```bash
python3 scripts/run_wired_oat.py --mode full-oat --run-tag test_plan --dry-run
```

### Custom seed

```bash
python3 scripts/run_wired_oat.py --mode full-oat --run-tag wired_seed2 --seed 2
```

### Enable verbose simulator print

```bash
python3 scripts/run_wired_oat.py --mode sanity --run-tag wired_sanity_verbose --verbose
```

---

## 8) Troubleshooting

### `FileNotFoundError: ns3`

Use the runner as provided; it resolves `./ns3` to an absolute path internally.

### No CWND graph data

Make sure sanity run uses `--enable-cwnd`.

### Build/config takes long each run

This is normal for ns-3 wrappers on some systems. Keep the same shell/workspace and reuse run tags logically.

---

## 9) Recommended execution order

1. Run sanity (`wired_sanity`)
2. Inspect sanity plots (especially `sanity_cwnd.png`)
3. Run full OAT (`wired_oat_full`)
4. Generate full OAT plots
5. Use `summary.csv` + plots for report tables/figures
