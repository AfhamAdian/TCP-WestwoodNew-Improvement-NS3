#!/usr/bin/env python3
"""
Plot metrics from TCP Westwood simulation
Generates graphs matching the paper format
"""

import matplotlib.pyplot as plt
import numpy as np
import sys
import os

def plot_throughput(filename='throughput.dat'):
    """Plot throughput over time"""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return
    
    try:
        data = np.loadtxt(filename, comments='#')
        time = data[:, 0]
        throughput = data[:, 1]
        
        plt.figure(figsize=(10, 6))
        plt.plot(time, throughput, 'b-', linewidth=1.5, label='TcpWestwoodPlus')
        plt.xlabel('Time (sec)', fontsize=12)
        plt.ylabel('Throughput (Kbps)', fontsize=12)
        plt.title('Throughput vs Time', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig('throughput.png', dpi=300)
        print("✓ Generated: throughput.png")
        plt.close()
    except Exception as e:
        print(f"Error plotting throughput: {e}")

def plot_losses(filename='losses.dat'):
    """Plot packet losses over time"""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return
    
    try:
        data = np.loadtxt(filename, comments='#')
        time = data[:, 0]
        losses = data[:, 1]
        
        plt.figure(figsize=(10, 6))
        plt.plot(time, losses, 'r-', linewidth=1.5, label='TcpWestwoodPlus')
        plt.xlabel('Time (sec)', fontsize=12)
        plt.ylabel('Packet Losses (cumulative)', fontsize=12)
        plt.title('Packet Losses vs Time', fontsize=14, fontweight='bold')
        plt.grid(True, alpha=0.3)
        plt.legend()
        plt.tight_layout()
        plt.savefig('losses.png', dpi=300)
        print("✓ Generated: losses.png")
        plt.close()
    except Exception as e:
        print(f"Error plotting losses: {e}")

def plot_cwnd(pattern='cwnd-*.dat'):
    """Plot congestion window for all flows"""
    import glob
    
    files = glob.glob(pattern)
    if not files:
        print(f"Warning: No files matching {pattern}")
        return
    
    plt.figure(figsize=(10, 6))
    
    colors = ['b', 'g', 'r', 'c', 'm', 'y']
    for idx, filename in enumerate(sorted(files)):
        try:
            data = np.loadtxt(filename, comments='#')
            if len(data) == 0:
                continue
            time = data[:, 0]
            cwnd = data[:, 1]
            
            flow_name = os.path.basename(filename).replace('.dat', '')
            plt.plot(time, cwnd, color=colors[idx % len(colors)], 
                    linewidth=1.0, label=flow_name, alpha=0.7)
        except Exception as e:
            print(f"Error reading {filename}: {e}")
    
    plt.xlabel('Time (sec)', fontsize=12)
    plt.ylabel('Congestion Window (segments)', fontsize=12)
    plt.title('Congestion Window vs Time', fontsize=14, fontweight='bold')
    plt.grid(True, alpha=0.3)
    plt.legend(fontsize=9)
    plt.tight_layout()
    plt.savefig('cwnd.png', dpi=300)
    print("✓ Generated: cwnd.png")
    plt.close()

def plot_delay(filename='delay.dat'):
    """Plot delay statistics"""
    if not os.path.exists(filename):
        print(f"Warning: {filename} not found")
        return
    
    try:
        # Read delay data (format: source -> dest \t delay)
        delays = []
        labels = []
        
        with open(filename, 'r') as f:
            for line in f:
                if line.startswith('#'):
                    continue
                parts = line.strip().split('\t')
                if len(parts) >= 2:
                    labels.append(parts[0])
                    delays.append(float(parts[1]))
        
        if delays:
            plt.figure(figsize=(10, 6))
            x = np.arange(len(delays))
            plt.bar(x, delays, color='skyblue', edgecolor='navy', alpha=0.7)
            plt.xlabel('Flow', fontsize=12)
            plt.ylabel('Average Delay (ms)', fontsize=12)
            plt.title('Average Delay per Flow', fontsize=14, fontweight='bold')
            plt.xticks(x, [f"Flow {i+1}" for i in range(len(delays))], rotation=45)
            plt.grid(True, alpha=0.3, axis='y')
            plt.tight_layout()
            plt.savefig('delay.png', dpi=300)
            print("✓ Generated: delay.png")
            plt.close()
    except Exception as e:
        print(f"Error plotting delay: {e}")

def create_summary_plot():
    """Create a 2x2 subplot with all metrics"""
    fig, ((ax1, ax2), (ax3, ax4)) = plt.subplots(2, 2, figsize=(14, 10))
    
    # Throughput
    try:
        data = np.loadtxt('throughput.dat', comments='#')
        ax1.plot(data[:, 0], data[:, 1], 'b-', linewidth=1.5)
        ax1.set_xlabel('Time (sec)')
        ax1.set_ylabel('Throughput (Kbps)')
        ax1.set_title('Throughput vs Time', fontweight='bold')
        ax1.grid(True, alpha=0.3)
    except:
        ax1.text(0.5, 0.5, 'No throughput data', ha='center', va='center')
    
    # Losses
    try:
        data = np.loadtxt('losses.dat', comments='#')
        ax2.plot(data[:, 0], data[:, 1], 'r-', linewidth=1.5)
        ax2.set_xlabel('Time (sec)')
        ax2.set_ylabel('Packet Losses')
        ax2.set_title('Packet Losses vs Time', fontweight='bold')
        ax2.grid(True, alpha=0.3)
    except:
        ax2.text(0.5, 0.5, 'No loss data', ha='center', va='center')
    
    # Cwnd
    import glob
    files = glob.glob('cwnd-*.dat')
    colors = ['b', 'g', 'r', 'c']
    for idx, filename in enumerate(sorted(files)[:4]):
        try:
            data = np.loadtxt(filename, comments='#')
            ax3.plot(data[:, 0], data[:, 1], color=colors[idx % len(colors)], 
                    linewidth=1.0, label=f'Flow {idx+1}', alpha=0.7)
        except:
            pass
    ax3.set_xlabel('Time (sec)')
    ax3.set_ylabel('Cwnd (segments)')
    ax3.set_title('Congestion Window vs Time', fontweight='bold')
    ax3.grid(True, alpha=0.3)
    ax3.legend(fontsize=9)
    
    # Delay
    try:
        delays = []
        with open('delay.dat', 'r') as f:
            for line in f:
                if not line.startswith('#'):
                    parts = line.strip().split('\t')
                    if len(parts) >= 2:
                        delays.append(float(parts[1]))
        
        if delays:
            x = np.arange(len(delays))
            ax4.bar(x, delays, color='skyblue', edgecolor='navy', alpha=0.7)
            ax4.set_xlabel('Flow')
            ax4.set_ylabel('Avg Delay (ms)')
            ax4.set_title('Average Delay per Flow', fontweight='bold')
            ax4.set_xticks(x)
            ax4.set_xticklabels([f'F{i+1}' for i in range(len(delays))])
            ax4.grid(True, alpha=0.3, axis='y')
    except:
        ax4.text(0.5, 0.5, 'No delay data', ha='center', va='center')
    
    plt.tight_layout()
    plt.savefig('summary.png', dpi=300)
    print("✓ Generated: summary.png (all metrics)")
    plt.close()

def main():
    print("\n=== Plotting TCP Metrics ===\n")
    
    plot_throughput()
    plot_losses()
    plot_cwnd()
    plot_delay()
    create_summary_plot()
    
    print("\n✓ All plots generated!")
    print("\nGenerated files:")
    print("  - throughput.png")
    print("  - losses.png")
    print("  - cwnd.png")
    print("  - delay.png")
    print("  - summary.png (combined view)")
    print()

if __name__ == '__main__':
    main()