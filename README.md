# NS-3 TCP Westwood+ Modification Project (Quick README)

## What this project is
Tweaking `TCP westwood plus` congestion control algorithm, improving throughput and packet loss.

## Modifications done
Custom congestion control logic was implemented in:
- `src/internet/model/tcp-dual-modified-tcp-westwoodplus-new.cc`

Key changes include:
- Bandwidth-ratio based congestion window behavior (`CalculateBWRatio`).
- Adaptive congestion avoidance:
  - Faster growth when bandwidth improves.
  - Normal additive increase under stable load.
  - Proportional decay when bandwidth drops.
- Smoothed RTT-based adaptive RTO estimation (`UpdateRtoEstimate`).
- Link-recovery signaling based on RTT ratio thresholds.


## TCP-WestwoodNew-Improvement-NS3 :
![Throughput vs Nodes](plots/wired_oat_requested/wired_oat_full/throughput_vs_nodes.png)
![Findings](<Overview and findings/Findings-Report.pdf>)


## Wired simulation setup done
The wired OAT experiments vary one factor at a time with these values:
- Nodes: 20, 40, 60, 80, 100
- Flows: 10, 20, 30, 40, 50
- Packet rate (pps): 100, 200, 300, 400, 500

Wired OAT execution modes:
- **Sanity mode:** 1 config × 3 variants
- **Full OAT mode:** 13 configs × 3 variants = 39 runs

A 40-second wired time-series setup is also included to compare:
- `TcpWestwoodPlus`
- `TcpWestwoodPlusNew`
- `TcpDualModifiedTcpWestwoodPlusNew`

## How to run wired simulations
From project root:

### 1) Wired OAT sanity run
```bash
python3 scripts/run_wired_oat.py --mode sanity --run-tag wired_sanity --simulation-time 20 --sampling-interval 2 --enable-cwnd
```

### 2) Wired full OAT run
```bash
python3 scripts/run_wired_oat.py --mode full-oat --run-tag wired_oat_full --simulation-time 20 --sampling-interval 5
```

### 3) Plot wired OAT
```bash
python3 scripts/plot_wired_oat.py --run-tag wired_oat_full --mode full-oat
python3 scripts/plot_wired_oat.py --run-tag wired_oat_full --mode requested
```

### 4) Wired 40s time-series run + plots
```bash
./ns3 run "wired-time-series-40s --simulationTime=40"
python3 scripts/plot_wired_time40.py
python3 scripts/plot_wired_time40_focus.py
python3 scripts/plot_wired_time40_three.py
```

## Output locations
- Data: `data/wired_oat/<run-tag>/`, `data/wired_time40/`
- Plots: `plots/wired_oat/<run-tag>/`, `plots/wired_oat_requested/<run-tag>/`, `plots/wired_time40/`
