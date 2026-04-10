#!/usr/bin/env python3

from pathlib import Path
import matplotlib.pyplot as plt

DATA_DIR = Path("data/wired_time40")
PLOT_DIR = Path("plots/wired_time40/focus_three")

VARIANTS = [
    "TcpWestwoodPlus",
    "TcpWestwoodPlusNew",
    "TcpDualModifiedTcpWestwoodPlusNew",
]


def load_time_series(path: Path):
    data = {}
    if not path.exists():
        return data

    with path.open() as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = line.split("\t")
            if len(parts) < 3:
                continue
            t = float(parts[0])
            v = float(parts[1])
            variant = parts[2].strip()
            if variant not in VARIANTS:
                continue
            data.setdefault(variant, [[], []])
            data[variant][0].append(t)
            data[variant][1].append(v)
    return data


def load_rtt_series():
    data = {}
    for file in sorted(DATA_DIR.glob("Tcp*-rtt.dat")):
        variant = file.stem.replace("-rtt", "")
        if variant not in VARIANTS:
            continue
        times, values = [], []
        with file.open() as f:
            for line in f:
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split("\t")
                if len(parts) < 2:
                    continue
                times.append(float(parts[0]))
                values.append(float(parts[1]))
        if times:
            data[variant] = [times, values]
    return data


def plot_lines(data, title, xlabel, ylabel, output):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for variant, (times, values) in sorted(data.items()):
        ax.plot(times, values, linestyle="-", linewidth=1.9, label=variant)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)
    print(f"Saved {output}")


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    queue = load_time_series(DATA_DIR / "queue_size_vs_time.dat")
    rtt = load_rtt_series()

    if queue:
        plot_lines(
            queue,
            "Queue Size vs Time (3 Algorithms)",
            "Time (s)",
            "Queue Size (packets)",
            PLOT_DIR / "queue_size_vs_time_three.png",
        )

    if rtt:
        plot_lines(
            rtt,
            "RTT vs Time (3 Algorithms)",
            "Time (s)",
            "RTT (s)",
            PLOT_DIR / "rtt_vs_time_three.png",
        )

    print(f"Plots written to {PLOT_DIR}")


if __name__ == "__main__":
    main()
