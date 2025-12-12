# UDPulse v1 — IoT Telemetry Protocol

## Project Overview

UDPulse v1 is a lightweight, loss-tolerant IoT telemetry protocol designed for constrained sensors. It operates over UDP and periodically reports sensor readings (temperature samples) to a central collector. The protocol prioritizes compact headers, low overhead, and robustness under packet loss, delay, and jitter.

This implementation fulfills **Project 1: IoT Telemetry Protocol (Sensor Reporting)** requirements for the CSE361 Computer Networks course.

---

## Key Features

- **Transport:** UDP (connectionless, loss-tolerant)
- **Message Types:** INIT, DATA, HEARTBEAT
- **Compact Binary Header:** 10 bytes
- **Optional Batching:** Multiple readings per DATA packet
- **Per-device State Tracking (Server)**
- **Duplicate Suppression & Gap Detection**
- **Timestamp-based Packet Reordering**
- **CSV Logging for Experimental Analysis**
- **Performance Metrics on Shutdown**

---

## Protocol Identification

- **Protocol Name:** UDPulse
- **Version:** 1
- **Encoding:** Big-endian (network byte order)

---

## Protocol Header Format

Total header size: **10 bytes**

| Field           | Size (bytes) | Type   | Description                   |
| --------------- | ------------ | ------ | ----------------------------- |
| Version         | 1            | uint8  | Protocol version (v1)         |
| Device ID       | 1            | uint8  | Unique device identifier      |
| Sequence Number | 2            | uint16 | Monotonic per-device sequence |
| Timestamp       | 4            | uint32 | Unix epoch time (seconds)     |
| Message Type    | 1            | uint8  | 0=INIT, 1=DATA, 2=HEARTBEAT   |
| Battery Health  | 1            | uint8  | Remaining battery percentage  |

Python struct format:

```
!B B H I B B
```

---

## Message Types

### INIT (Type = 0)

- Sent once at client startup
- Device ID initially set to `0`
- Server assigns a unique Device ID and responds

### DATA (Type = 1)

- Carries one or more temperature readings
- Payload format:
  - Single reading: `"36"`
  - Batched readings: `"36,37,38"`

### HEARTBEAT (Type = 2)

- Sent periodically when no DATA is available
- Indicates device liveness
- Payload: `alive`

---

## Client Design

### Responsibilities

- Generate periodic temperature readings
- Optionally batch readings into one packet
- Maintain sequence number and battery level
- Send HEARTBEAT packets independently of DATA

### Configuration (CLI Arguments)

| Argument                   | Description                                  | Default |
| -------------------------- | -------------------------------------------- | ------- |
| `-b, --batch`              | Number of readings per DATA packet           | 1       |
| `-d, --data_interval`      | Interval between sensor readings (seconds)   | 4       |
| `-H, --heartbeat_interval` | Interval between HEARTBEAT packets (seconds) | 1       |

### Example

```bash
python3 client.py -b 3 -d 2 -H 1
```

---

## Server Design

### Responsibilities

- Assign device IDs during INIT
- Maintain per-device state:
  - Last sequence number
  - Received packet count
  - Duplicate count
  - Gap count
- Reorder packets using a time window
- Detect duplicates and sequence gaps
- Log all packets to CSV
- Compute performance metrics

### Packet Reordering

- Packets are buffered in a min-heap ordered by sensor timestamp
- A **50 ms reorder window** ensures late packets are reordered correctly

---

## CSV Logging

All received packets are logged to `telemetry_log.csv` with the following fields:

| Field           | Description                              |
| --------------- | ---------------------------------------- |
| device\_id      | Assigned device ID                       |
| seq             | Packet sequence number                   |
| timestamp       | Sensor timestamp (YYYY-MM-DD HH\:MM\:SS) |
| arrival\_time   | Server arrival time (with milliseconds)  |
| duplicate\_flag | 1 if duplicate, else 0                   |
| gap\_flag       | 1 if sequence gap detected, else 0       |

---

## Metrics Collected (On Server Shutdown)

| Metric               | Description                     |
| -------------------- | ------------------------------- |
| packets\_received    | Total processed packets         |
| bytes\_per\_report   | Avg bytes per valid DATA report |
| duplicate\_rate      | duplicates / packets\_received  |
| sequence\_gap\_count | Total missing sequence numbers  |
| cpu\_ms\_per\_report | CPU time per processed report   |

Metrics are printed automatically when the server is terminated with **Ctrl+C**.

---

## Running the System

### 1. Start the Server

```bash
python3 server.py
```

### 2. Start One or More Clients

```bash
python3 client.py
```

---

## Testing & Network Impairment Experiments

The protocol is tested under controlled network impairments using **Linux ****tc netem**.

### Manual netem Commands (loopback interface)

```bash
# 5% Packet Loss
sudo tc qdisc add dev lo root netem loss 5%

# Delay + Jitter (100ms ±10ms)
sudo tc qdisc add dev lo root netem delay 100ms 10ms

# Packet Duplication (10%)
sudo tc qdisc add dev lo root netem duplicate 10%

# Packet Reordering (25% reordered, delayed)
sudo tc qdisc add dev lo root netem reorder 25% delay 30ms 10ms

# Check active rules
sudo tc qdisc show dev lo

# Reset / remove netem
sudo tc qdisc del dev lo root
```

---

## Automated Test Execution

To ensure reproducibility, the project includes scripts that automatically apply netem rules and run the client and server.

### Files

```text
tests/netem.sh
run_experiment.sh
```

### Run Experiments

```bash
# Baseline (no impairment)
./run_experiment.sh none

# 5% Packet Loss
./run_experiment.sh loss

# Delay + Jitter
./run_experiment.sh delay

# Packet Duplication
./run_experiment.sh duplicate

# Packet Reordering
./run_experiment.sh reorder
```

Each run produces:

```text
server_<mode>_<timestamp>.log
client_<mode>_<timestamp>.log
telemetry_log.csv
```

---

## Expected Test Behavior

| Scenario       | Expected Result                            |
| -------------- | ------------------------------------------ |
| Baseline       | ≥99% packets received, ordered             |
| Loss 5%        | Sequence gaps detected, duplicate rate ≤1% |
| Delay + Jitter | Correct reordering by timestamp            |
| Duplicate      | Duplicate packets suppressed               |
| Reorder        | No crashes, ordered delivery               |

---

## Design Rationale

- **UDP:** Low overhead and supports loss experiments
- **No Retransmission:** Detect-only loss model
- **Sequence Numbers:** Enable duplicate & gap detection
- **Batching:** Reduces per-reading overhead
- **Epoch Timestamps:** Simple and efficient ordering

---

## Environment

- Python 3.8+
- Tested on Linux, macOS
- Uses only standard libraries

---

## Academic Integrity

This protocol and implementation are original and designed specifically for the CSE361 course. No external networking frameworks or third-party protocol libraries were used.

---

## Authors

> Course Project — Computer Networks (CSE361)
- Karim Marwan Wahid
- Adam Heshmat Makram
- Yousef Waleed Anwar
- Mohamed Sameh Sayed
- Aly Ahmed Ali Attia

