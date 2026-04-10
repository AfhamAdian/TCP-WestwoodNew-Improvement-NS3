# NS2 Project Submission Checklist

## Submittables

- Full repository of code  
- A comprehensive project report  
- Zip them together and submit on Moodle  

---

## Experimentation

Simulate the following networks with your implemented algorithm as per your ID:

- Wired  
- Wireless 802.15.4 (static)  

---

## Simulation Parameters

The number of nodes need to be varied as:

- 20, 40, 60, 80, and 100  

Besides, you need to vary the following parameters:

### Number of flows
- 10, 20, 30, 40, and 50  

### Number of packets per second
- 100, 200, 300, 400, and 500  

### Speed of nodes (only for mobile cases)
- 5 m/s, 10 m/s, 15 m/s, 20 m/s, and 25 m/s  

### Coverage area (only for static nodes)
- Square coverage area varying one side as:
  - Tx_range
  - 2 × Tx_range
  - 3 × Tx_range
  - 4 × Tx_range
  - 5 × Tx_range  

---

## Required Metrics

In all cases, you need to measure the following metrics and plot graphs:

- Network throughput  
- End-to-end delay  
- Packet delivery ratio  
  - (total number of packets delivered to end destination / total number of packets sent)  
- Packet drop ratio  
  - (total number of packets dropped / total number of packets sent)  
- Energy consumption (for wireless nodes)  

---



(YOU DONT NEED TO WRITE REPORT. I WILL FOCUS ON CODING FIRST. JUST MAKE SURE I HAVE THE DATA READY TO MAKE THE REPORT LATER.)
## Report Requirements

You need to submit a report mentioning the following:

- Network topologies under simulation  
- Parameters under variation  
- Modifications made in the simulator  
- Results with graphs  
- Summary findings  
- Reflection on findings (Discussion)  

---



## Bonus (Selected) ( I DONT NEED BONUS RIGHT NOW. DONT PLAN FOR THIS)

### Extra Metrics

You can get bonus marks by measuring any metric not mentioned above.

Examples include:

- Per-node throughput  
- Variation in queue size over time  
- Any additional meaningful performance metric  
