#!/usr/bin/env python3
"""
Robust TCP comparison plotter.
- Reads .dat files from  data/
- Writes .png files into plots/
- Auto-detects all TCP variants from .dat files
- Extra focused plots: Westwood vs WestwoodNew only
"""

import matplotlib.pyplot as plt
import numpy as np
import os
import glob
import re
from collections import defaultdict

DAT_DIR  = 'data'
PLOT_DIR = 'plots'

# ── Smoothing window (increase for smoother lines, 1 = no smoothing) ────────
SMOOTH_WINDOW = 2

# ── Color palette ───────────────────────────────────────────────────────────
COLORS = [
    '#1f77b4',  # blue
    '#d62728',  # red
    '#2ca02c',  # green
    '#ff7f0e',  # orange
    '#9467bd',  # purple
    '#8c564b',  # brown
    '#e377c2',  # pink
    '#17becf',  # cyan
    '#bcbd22',  # yellow-green
    '#7f7f7f',  # grey
]

def get_color_map(variants):
    return {v: COLORS[i % len(COLORS)] for i, v in enumerate(sorted(variants))}

def moving_average(values, window=SMOOTH_WINDOW):
    if len(values) < window:
        return values
    kernel = np.ones(window) / window
    padded = np.pad(values, (window // 2, window // 2), mode='edge')
    return np.convolve(padded, kernel, mode='valid')[:len(values)]

def out(filename):
    """Return full path for a plot output file."""
    return os.path.join(PLOT_DIR, filename)


# ── Data loaders ────────────────────────────────────────────────────────────

def load_throughput():
    filepath = os.path.join(DAT_DIR, 'comparison_throughput.dat')
    data = defaultdict(lambda: ([], []))
    if not os.path.exists(filepath):
        print(f"  [skip] {filepath} not found")
        return data
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                try:
                    t, val, variant = float(parts[0]), float(parts[1]), parts[2].strip()
                    data[variant][0].append(t)
                    data[variant][1].append(val)
                except ValueError:
                    continue
    return data


def load_losses():
    filepath = os.path.join(DAT_DIR, 'comparison_losses.dat')
    data = defaultdict(lambda: ([], []))
    if not os.path.exists(filepath):
        print(f"  [skip] {filepath} not found")
        return data
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            try:
                t, val = float(parts[0]), float(parts[1])
                variant = parts[2].strip() if len(parts) >= 3 else 'Combined'
                data[variant][0].append(t)
                data[variant][1].append(val)
            except ValueError:
                continue
    return data


def load_delay():
    filepath = os.path.join(DAT_DIR, 'comparison_delay.dat')
    data = defaultdict(lambda: ([], []))
    if not os.path.exists(filepath):
        print(f"  [skip] {filepath} not found")
        return data
    with open(filepath) as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            parts = line.split('\t')
            if len(parts) >= 3:
                try:
                    t, val, variant = float(parts[0]), float(parts[1]), parts[2].strip()
                    data[variant][0].append(t)
                    data[variant][1].append(val)
                except ValueError:
                    continue
    return data


def load_cwnd_files():
    data = {}
    pattern = os.path.join(DAT_DIR, 'Tcp*-cwnd.dat')
    for filepath in sorted(glob.glob(pattern)):
        basename = os.path.basename(filepath)
        match = re.match(r'^(.+?)-cwnd\.dat$', basename)
        variant = match.group(1) if match else basename
        try:
            raw = np.loadtxt(filepath, comments='#')
            if raw.ndim == 2 and raw.shape[1] >= 2 and len(raw) > 0:
                data[variant] = (raw[:, 0].tolist(), raw[:, 1].tolist())
            elif raw.ndim == 1 and len(raw) >= 2:
                data[variant] = ([raw[0]], [raw[1]])
        except Exception as e:
            print(f"  [warn] Could not read {filepath}: {e}")
    return data


# ── Plot helpers ────────────────────────────────────────────────────────────

def _finalize(ax, xlabel, ylabel, title, outfile, fig=None):
    ax.set_xlabel(xlabel, fontsize=12)
    ax.set_ylabel(ylabel, fontsize=12)
    ax.set_title(title, fontsize=13, fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)
    if fig:
        fig.tight_layout()
        fig.savefig(outfile, dpi=300)
        plt.close(fig)

def _plot_lines(ax, data, colors, smooth_window=SMOOTH_WINDOW):
    for variant, (times, vals) in sorted(data.items()):
        smooth = moving_average(np.array(vals), window=smooth_window)
        ax.plot(times, smooth, color=colors[variant], linewidth=1.8,
                label=variant, alpha=0.9)


# ── All-variants plots ──────────────────────────────────────────────────────

def plot_throughput_comparison():
    # print("\n[Throughput — all variants]")
    data = load_throughput()
    if not data:
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_lines(ax, data, colors)
    _finalize(ax, 'Time (s)', 'Throughput (Kbps)',
              'Throughput Comparison', out('comparison_throughput.png'), fig)

    print("\n  Average throughput:")
    baseline_val = None
    for variant, (_, vals) in sorted(data.items()):
        avg = np.mean(vals)
        if baseline_val is None:
            baseline_val = avg
            print(f"    {variant:<30s} {avg:>10.2f} Kbps  (baseline)")
        else:
            diff = (avg - baseline_val) / baseline_val * 100
            print(f"    {variant:<30s} {avg:>10.2f} Kbps  ({diff:+.1f}%)")


def plot_cwnd_comparison():
    data = load_cwnd_files()
    if not data:
        print("  [skip] No Tcp*-cwnd.dat files found")
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_lines(ax, data, colors)
    _finalize(ax, 'Time (s)', 'Congestion Window (bytes)',
              'Congestion Window Comparison', out('comparison_cwnd.png'), fig)


def plot_losses_comparison():
    data = load_losses()
    if not data:
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    for variant, (times, losses) in sorted(data.items()):
        ax.plot(times, losses, color=colors[variant], linewidth=1.5,
                label=variant, alpha=0.8)
    _finalize(ax, 'Time (s)', 'Packet Losses (cumulative)',
              'Packet Losses Over Time', out('comparison_losses.png'), fig)


def plot_delay_comparison():
    data = load_delay()
    if not data:
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    for variant, (times, delays) in sorted(data.items()):
        # Cumulative sum of per-interval average delays → rising curve like the paper
        cumulative = np.cumsum(delays)
        ax.plot(times, cumulative, color=colors[variant], linewidth=1.8,
                label=variant, alpha=0.9)
    _finalize(ax, 'Time (s)', 'Delay (s)',
              'Delay of mechanisms', out('comparison_delay.png'), fig)


# ── Focused Westwood-only plots ─────────────────────────────────────────────

WESTWOOD_VARIANTS = {'TcpWestwoodPlus', 'TcpWestwoodPlusNew'}
WESTWOOD_MODIFIED_VARIANTS = {
    'TcpWestwoodPlus',
    'TcpWestwoodPlusNew',
    'TcpModifiedTcoWestwoodPlusNew',
}

def plot_westwood_throughput():
    all_data = load_throughput()
    data = {k: v for k, v in all_data.items() if k in WESTWOOD_VARIANTS}
    if not data:
        print("  [skip] No Westwood data found in throughput file")
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_lines(ax, data, colors)
    _finalize(ax, 'Time (s)', 'Throughput (Kbps)',
              'Throughput: WestwoodPlus vs WestwoodPlusNew',
              out('westwood_throughput.png'), fig)


def plot_westwood_cwnd():
    all_data = load_cwnd_files()
    data = {k: v for k, v in all_data.items() if k in WESTWOOD_VARIANTS}
    if not data:
        print("  [skip] No Westwood cwnd files found")
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_lines(ax, data, colors)
    _finalize(ax, 'Time (s)', 'Congestion Window (bytes)',
              'Cwnd: WestwoodPlus vs WestwoodPlusNew',
              out('westwood_cwnd.png'), fig)


def plot_westwood_modified_throughput():
    all_data = load_throughput()
    data = {k: v for k, v in all_data.items() if k in WESTWOOD_MODIFIED_VARIANTS}
    if not data:
        print("  [skip] No Westwood/Modified data found in throughput file")
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_lines(ax, data, colors)
    _finalize(ax, 'Time (s)', 'Throughput (Kbps)',
              'Throughput: WestwoodPlus vs WestwoodPlusNew vs ModifiedTcoWestwoodPlusNew',
              out('westwood_modified_throughput.png'), fig)


def plot_westwood_modified_cwnd():
    all_data = load_cwnd_files()
    data = {k: v for k, v in all_data.items() if k in WESTWOOD_MODIFIED_VARIANTS}
    if not data:
        print("  [skip] No Westwood/Modified cwnd files found")
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    _plot_lines(ax, data, colors)
    _finalize(ax, 'Time (s)', 'Congestion Window (bytes)',
              'Cwnd: WestwoodPlus vs WestwoodPlusNew vs ModifiedTcoWestwoodPlusNew',
              out('westwood_modified_cwnd.png'), fig)


def plot_westwood_modified_losses():
    all_data = load_losses()
    data = {k: v for k, v in all_data.items() if k in WESTWOOD_MODIFIED_VARIANTS}
    if not data:
        print("  [skip] No Westwood/Modified data found in losses file")
        return
    colors = get_color_map(data.keys())
    fig, ax = plt.subplots(figsize=(12, 6))
    for variant, (times, losses) in sorted(data.items()):
        ax.plot(times, losses, color=colors[variant], linewidth=1.5,
                label=variant, alpha=0.85)
    _finalize(ax, 'Time (s)', 'Packet Losses (cumulative)',
              'Losses: WestwoodPlus vs WestwoodPlusNew vs ModifiedTcoWestwoodPlusNew',
              out('westwood_modified_losses.png'), fig)


# ── Summary (throughput + cwnd only, no losses/bar) ─────────────────────────

def create_summary():
    tp_data   = load_throughput()
    cwnd_data = load_cwnd_files()

    all_variants = set(tp_data) | set(cwnd_data)
    if not all_variants:
        print("  [skip] No data found for summary")
        return

    colors = get_color_map(all_variants)
    fig, axes = plt.subplots(1, 2, figsize=(18, 6))
    fig.suptitle('TCP Variants — Full Comparison', fontsize=15, fontweight='bold')

    ax = axes[0]
    _plot_lines(ax, tp_data, colors)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Throughput (Kbps)')
    ax.set_title('Throughput', fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    _plot_lines(ax, cwnd_data, colors)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Cwnd (bytes)')
    ax.set_title('Congestion Window', fontweight='bold')
    ax.legend(fontsize=9)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    path = out('comparison_summary.png')
    fig.savefig(path, dpi=300)
    plt.close(fig)


# ── Westwood-only side-by-side summary ──────────────────────────────────────

def create_westwood_summary():
    """Side-by-side Throughput | Cwnd for WestwoodPlus vs WestwoodPlusNew only."""
    all_tp   = load_throughput()
    all_cwnd = load_cwnd_files()

    tp_data   = {k: v for k, v in all_tp.items()   if k in WESTWOOD_VARIANTS}
    cwnd_data = {k: v for k, v in all_cwnd.items() if k in WESTWOOD_VARIANTS}

    if not tp_data and not cwnd_data:
        print("  [skip] No Westwood data for summary")
        return

    colors = get_color_map(WESTWOOD_VARIANTS)
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))
    fig.suptitle('WestwoodPlus vs WestwoodPlusNew', fontsize=14, fontweight='bold')

    ax = axes[0]
    _plot_lines(ax, tp_data, colors)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Throughput (Kbps)')
    ax.set_title('Throughput', fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    ax = axes[1]
    _plot_lines(ax, cwnd_data, colors)
    ax.set_xlabel('Time (s)')
    ax.set_ylabel('Congestion Window (bytes)')
    ax.set_title('Congestion Window', fontweight='bold')
    ax.legend(fontsize=10)
    ax.grid(True, alpha=0.3)

    fig.tight_layout()
    path = out('westwood_summary.png')
    fig.savefig(path, dpi=300)
    plt.close(fig)


# ── Average throughput bar chart (auto-scaled Y axis) ───────────────────────

def plot_avg_throughput_bar():
    """Bar chart of average throughput per variant, Y-axis scaled to show small differences."""
    data = load_throughput()
    if not data:
        return

    variants = sorted(data.keys())
    avgs     = [np.mean(data[v][1]) for v in variants]
    colors   = [COLORS[i % len(COLORS)] for i in range(len(variants))]

    fig, ax = plt.subplots(figsize=(10, 5))

    bars = ax.bar(variants, avgs, color=colors, width=0.5, edgecolor='black', linewidth=0.6)

    # Annotate each bar with its value
    for bar, val in zip(bars, avgs):
        ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + 0.002 * max(avgs),
                f'{val:.1f}', ha='center', va='bottom', fontsize=10, fontweight='bold')

    # Scale Y axis to emphasise small differences:
    # set bottom to 95% of min value, top to 105% of max
    y_min = min(avgs)
    y_max = max(avgs)
    margin = (y_max - y_min) * 0.5 if y_max != y_min else y_max * 0.05
    ax.set_ylim(y_min - margin * 2, y_max + margin * 4)

    ax.set_xlabel('TCP Variant', fontsize=12)
    ax.set_ylabel('Average Throughput (Kbps)', fontsize=12)
    ax.set_title('Average Throughput per Variant', fontsize=13, fontweight='bold')
    ax.tick_params(axis='x', rotation=15)
    ax.grid(True, axis='y', alpha=0.3)

    fig.tight_layout()
    path = out('avg_throughput_bar.png')
    fig.savefig(path, dpi=300)
    plt.close(fig)


# ── Main ────────────────────────────────────────────────────────────────────

def main():
    os.makedirs(PLOT_DIR, exist_ok=True)

    print("=" * 55)
    print("  TCP Variant Comparison Plotter")
    print(f"  data dir : {DAT_DIR}/")
    print(f"  plots dir: {PLOT_DIR}/")
    print("=" * 55)

    cwnd_files = sorted(glob.glob(os.path.join(DAT_DIR, 'Tcp*-cwnd.dat')))
    detected = [re.match(r'^(.+?)-cwnd\.dat$', os.path.basename(f)).group(1)
                for f in cwnd_files]
    if detected:
        print(f"\nDetected variants: {', '.join(detected)}")

    # All-variants plots
    plot_throughput_comparison()
    plot_cwnd_comparison()
    plot_losses_comparison()
    plot_delay_comparison()
    create_summary()

    # Focused Westwood-only plots
    plot_westwood_throughput()
    plot_westwood_cwnd()

    # Focused Westwood + Modified plots
    plot_westwood_modified_throughput()
    plot_westwood_modified_cwnd()
    plot_westwood_modified_losses()

    # Additional: Westwood side-by-side summary + average throughput bar
    create_westwood_summary()
    plot_avg_throughput_bar()


if __name__ == '__main__':
    main()