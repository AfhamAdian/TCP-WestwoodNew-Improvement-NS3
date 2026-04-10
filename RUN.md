## 1) Wired OAT (nodes / flows / packet rate)

### Sanity run (1 config × 3 variants)
```bash
python3 scripts/run_wired_oat.py --mode sanity --run-tag wired_sanity --simulation-time 20 --sampling-interval 2 --enable-cwnd
```

### Full OAT run (13 configs × 3 variants = 39 runs)
```bash
python3 scripts/run_wired_oat.py --mode full-oat --run-tag wired_oat_full --simulation-time 20 --sampling-interval 5
```

### Plot wired OAT
```bash
# sanity plots
python3 scripts/plot_wired_oat.py --run-tag wired_sanity --mode sanity

# full OAT plots
python3 scripts/plot_wired_oat.py --run-tag wired_oat_full --mode full-oat

# requested format plots in separate dir
python3 scripts/plot_wired_oat.py --run-tag wired_oat_full --mode requested
```

Outputs:
- Data: `data/wired_oat/<run-tag>/`
- Plots: `plots/wired_oat/<run-tag>/`
- Requested plots: `plots/wired_oat_requested/<run-tag>/`

---

## 2) Wireless 802.15.4 static OAT

### Sanity run (1 config × 3 variants)
```bash
python3 scripts/run_wireless_oat.py --mode sanity --run-tag wireless_sanity --simulation-time 20
```

### Full OAT + coverage run
Includes one-factor sweeps for:
- nodes (20,40,60,80,100)
- flows (10,20,30,40,50)
- packet rate (100,200,300,400,500)
- coverage multiplier (1,2,3,4,5)

Total = 17 configs × 3 variants = 51 runs.

```bash
python3 scripts/run_wireless_oat.py --mode full-oat --run-tag wireless_oat_full_cov --simulation-time 20
```

### Plot wireless requested graphs
```bash
python3 scripts/plot_wireless_oat.py --run-tag wireless_oat_full_cov
```

Outputs:
- Data: `data/wireless_oat/<run-tag>/`
- Plots: `plots/wireless_oat_requested/<run-tag>/`

---

## 3) Wired 40s time-series simulator

This compares:
- `TcpWestwoodPlus`
- `TcpWestwoodPlusNew`
- `TcpDualModifiedTcpWestwoodPlusNew`

Metrics over time:
- Throughput
- Delay
- Packet Loss
- CWND
- Queue Size (bottleneck)
- RTT

### Run simulator (40 seconds)
```bash
./ns3 run "wired-time-series-40s --simulationTime=40"
```

### Plot all 3-algorithm time-series graphs
```bash
python3 scripts/plot_wired_time40.py
```

Outputs:
- Data: `data/wired_time40/`
- Plots: `plots/wired_time40/`

---

## 4) Focused queue/RTT plots

### 2-algorithm focused plots (outside current dir)
Compares:
- `TcpWestwoodPlusNew`
- `TcpDualModifiedTcpWestwoodPlusNew`

```bash
python3 scripts/plot_wired_time40_focus.py
```

Outputs:
- `plots/wired_time40_focus/queue_size_vs_time_focus.png`
- `plots/wired_time40_focus/rtt_vs_time_focus.png`

### 3-algorithm queue/RTT plots (nested dir)
```bash
python3 scripts/plot_wired_time40_three.py
```

Outputs:
- `plots/wired_time40/focus_three/queue_size_vs_time_three.png`
- `plots/wired_time40/focus_three/rtt_vs_time_three.png`

---

## 5) Quick full rerun sequence

If you want to refresh wired 40s data + plots quickly:
```bash
./ns3 run "wired-time-series-40s --simulationTime=40"
python3 scripts/plot_wired_time40.py
python3 scripts/plot_wired_time40_focus.py
python3 scripts/plot_wired_time40_three.py
```

If you want to refresh wireless full run + plots:
```bash
python3 scripts/run_wireless_oat.py --mode full-oat --run-tag wireless_oat_full_cov --simulation-time 20
python3 scripts/plot_wireless_oat.py --run-tag wireless_oat_full_cov
```
