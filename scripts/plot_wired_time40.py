#!/usr/bin/env python3

from pathlib import Path
import matplotlib.pyplot as plt

DATA_DIR = Path("data/wired_time40")
PLOT_DIR = Path("plots/wired_time40")


def load_metric_file(path: Path):
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
            data.setdefault(variant, [[], []])
            data[variant][0].append(t)
            data[variant][1].append(v)
    return data


def load_cwnd_files():
    data = {}
    for file in sorted(DATA_DIR.glob("Tcp*-cwnd.dat")):
        variant = file.name.replace("-cwnd.dat", "")
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


def load_variant_trace_files(pattern: str):
    data = {}
    for file in sorted(DATA_DIR.glob(pattern)):
        variant = file.stem.replace("-rtt", "")
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


def load_variant_file(filename: str):
    data = {}
    path = DATA_DIR / filename
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
            times = data.setdefault(parts[2].strip(), [[], []])
            times[0].append(float(parts[0]))
            times[1].append(float(parts[1]))
    return data


def plot_lines(data, title, xlabel, ylabel, output):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for variant, (times, values) in sorted(data.items()):
        ax.plot(times, values, linestyle="-", linewidth=1.8, label=variant)

    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)
    print(f"Saved {output}")


def plot_delay_cumulative(data, output):
    fig, ax = plt.subplots(figsize=(11, 5.5))
    for variant, (times, values) in sorted(data.items()):
        ax.plot(times, values, linestyle="-", linewidth=1.8, label=variant)

    ax.set_title("Delay vs Time (40s)")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Cumulative Delay Sum (s)")
    ax.grid(alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig(output, dpi=220)
    plt.close(fig)
    print(f"Saved {output}")


def print_summary_stats(throughput, delay, loss, rtt, queue):
    variants = sorted(set(throughput) | set(delay) | set(loss) | set(rtt) | set(queue))
    print("\nSummary per algorithm:")
    for variant in variants:
        thr_vals = throughput.get(variant, [[], []])[1]
        dly_vals = delay.get(variant, [[], []])[1]
        los_vals = loss.get(variant, [[], []])[1]
        rtt_vals = rtt.get(variant, [[], []])[1]
        q_vals = queue.get(variant, [[], []])[1]

        avg_throughput = sum(thr_vals) / len(thr_vals) if thr_vals else 0.0
        final_delay = dly_vals[-1] if dly_vals else 0.0
        final_loss = los_vals[-1] if los_vals else 0.0
        avg_rtt = sum(rtt_vals) / len(rtt_vals) if rtt_vals else 0.0
        avg_queue = sum(q_vals) / len(q_vals) if q_vals else 0.0
        max_queue = max(q_vals) if q_vals else 0.0

        print(f"  {variant}")
        print(f"    Avg throughput : {avg_throughput:.3f} Kbps")
        print(f"    Final delay    : {final_delay:.6f} s")
        print(f"    Final loss     : {final_loss:.0f} packets")
        print(f"    Avg RTT        : {avg_rtt:.6f} s")
        print(f"    Avg queue size : {avg_queue:.3f} packets")
        print(f"    Max queue size : {max_queue:.0f} packets")


def main():
    PLOT_DIR.mkdir(parents=True, exist_ok=True)

    throughput = load_metric_file(DATA_DIR / "throughput_vs_time.dat")
    delay = load_metric_file(DATA_DIR / "delay_vs_time.dat")
    loss = load_metric_file(DATA_DIR / "packet_loss_vs_time.dat")
    cwnd = load_cwnd_files()
    queue = load_metric_file(DATA_DIR / "queue_size_vs_time.dat")
    rtt = load_variant_trace_files("Tcp*-rtt.dat")

    if throughput:
        plot_lines(
            throughput,
            "Throughput vs Time (40s)",
            "Time (s)",
            "Throughput (Kbps)",
            PLOT_DIR / "throughput_vs_time.png",
        )

    if delay:
        plot_delay_cumulative(delay, PLOT_DIR / "delay_vs_time.png")

    if loss:
        plot_lines(
            loss,
            "Packet Loss vs Time (40s)",
            "Time (s)",
            "Packet Loss (cumulative)",
            PLOT_DIR / "packet_loss_vs_time.png",
        )

    if cwnd:
        plot_lines(
            cwnd,
            "CWND vs Time (40s)",
            "Time (s)",
            "Congestion Window (bytes)",
            PLOT_DIR / "cwnd_vs_time.png",
        )

    if queue:
        plot_lines(
            queue,
            "Queue Size vs Time (40s)",
            "Time (s)",
            "Queue Size (packets)",
            PLOT_DIR / "queue_size_vs_time.png",
        )

    if rtt:
        plot_lines(
            rtt,
            "RTT vs Time (40s)",
            "Time (s)",
            "RTT (s)",
            PLOT_DIR / "rtt_vs_time.png",
        )

    print_summary_stats(throughput, delay, loss, rtt, queue)

    print(f"Plots written to {PLOT_DIR}")


if __name__ == "__main__":
    main()
