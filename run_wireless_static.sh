#!/usr/bin/env bash
# ============================================================================
# run_wireless_static.sh — Automate wireless static network simulations
#
# Usage:
#   bash run_wireless_static.sh          # full sweep
#   bash run_wireless_static.sh --test   # quick test (2 nodes values, 1 variant)
# ============================================================================

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# ── Configuration ──
VARIANTS=("TcpDualModifiedTcpWestwoodPlusNew" "TcpWestwoodPlusNew" "TcpWestwoodPlus")
SIM_TIME=30

# Default values (used when not varying that parameter)
DEF_NODES=40
DEF_FLOWS=20
DEF_PPS=200
DEF_COV=2

# Sweep ranges
NODES_LIST=(20 40 60 80 100)
FLOWS_LIST=(10 20 30 40 50)
PPS_LIST=(100 200 300 400 500)
COV_LIST=(1 2 3 4 5)

# Output
RESULTS_DIR="results_wireless_static"
CSV_FILE="${RESULTS_DIR}/summary.csv"

# ── Test mode ──
TEST_MODE=false
if [[ "${1:-}" == "--test" ]]; then
    TEST_MODE=true
    VARIANTS=("TcpWestwoodPlus")
    NODES_LIST=(20 40)
    FLOWS_LIST=(10 20)
    PPS_LIST=(100 200)
    COV_LIST=(1 2)
    SIM_TIME=20
    echo ">>> TEST MODE: reduced parameter sweep"
fi

# ── Build ──
echo "========================================="
echo "  Building ns-3..."
echo "========================================="
./ns3 build 2>&1 | tail -5

# ── Prepare output ──
mkdir -p "$RESULTS_DIR"
echo "tcpVariant,nNodes,nFlows,packetsPerSecond,coverageMultiplier,throughput_kbps,avgDelay_ms,pdr_percent,dropRatio_percent,energy_joules" > "$CSV_FILE"

run_one() {
    local variant="$1" nodes="$2" flows="$3" pps="$4" cov="$5"
    echo "  ▸ ${variant}  nodes=${nodes} flows=${flows} pps=${pps} cov=${cov}×Tx"

    local line
    line=$(./ns3 run "wireless-static-sim \
        --tcpVariant=${variant} \
        --nNodes=${nodes} \
        --nFlows=${flows} \
        --packetsPerSecond=${pps} \
        --coverageMultiplier=${cov} \
        --simulationTime=${SIM_TIME}" 2>/dev/null | tail -1)

    if [[ -n "$line" ]]; then
        echo "$line" >> "$CSV_FILE"
    else
        echo "    ⚠ No output for this run"
    fi
}

total_runs=0
completed=0

# Count total
for variant in "${VARIANTS[@]}"; do
    total_runs=$(( total_runs + ${#NODES_LIST[@]} + ${#FLOWS_LIST[@]} + ${#PPS_LIST[@]} + ${#COV_LIST[@]} ))
done

echo ""
echo "========================================="
echo "  Starting $total_runs simulation runs"
echo "========================================="
echo ""

for variant in "${VARIANTS[@]}"; do
    echo "── Variant: ${variant} ──"

    # 1) Vary nodes
    echo "  [1/4] Varying nodes..."
    for n in "${NODES_LIST[@]}"; do
        run_one "$variant" "$n" "$DEF_FLOWS" "$DEF_PPS" "$DEF_COV"
        completed=$((completed + 1))
        echo "    Progress: ${completed}/${total_runs}"
    done

    # 2) Vary flows
    echo "  [2/4] Varying flows..."
    for f in "${FLOWS_LIST[@]}"; do
        run_one "$variant" "$DEF_NODES" "$f" "$DEF_PPS" "$DEF_COV"
        completed=$((completed + 1))
        echo "    Progress: ${completed}/${total_runs}"
    done

    # 3) Vary packets per second
    echo "  [3/4] Varying packets/s..."
    for p in "${PPS_LIST[@]}"; do
        run_one "$variant" "$DEF_NODES" "$DEF_FLOWS" "$p" "$DEF_COV"
        completed=$((completed + 1))
        echo "    Progress: ${completed}/${total_runs}"
    done

    # 4) Vary coverage area
    echo "  [4/4] Varying coverage..."
    for c in "${COV_LIST[@]}"; do
        run_one "$variant" "$DEF_NODES" "$DEF_FLOWS" "$DEF_PPS" "$c"
        completed=$((completed + 1))
        echo "    Progress: ${completed}/${total_runs}"
    done

    echo ""
done

echo "========================================="
echo "  All simulations complete!"
echo "  CSV: ${CSV_FILE}"
echo "========================================="
echo ""

# ── Plotting ──
echo "Generating plots..."
python3 plot_wireless_static.py
echo "Done! Check plots_wireless_static/"
