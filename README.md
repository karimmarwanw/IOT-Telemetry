# UDPulse v1 — IoT Telemetry Protocol (Phase 1)

## 📘 Overview
**UDPulse v1** is a lightweight, custom telemetry protocol designed for constrained IoT sensors that send periodic readings to a central collector over **UDP**.  
It focuses on **low overhead**, **loss tolerance**, and **efficient performance** in unreliable or bandwidth-limited networks.

Both **client** and **server** components are implemented in **Python** using socket-based communication.

---

## 🚀 Motivation
Standard IoT protocols (like MQTT or CoAP) introduce overhead and reliability mechanisms that aren’t ideal for:
- Battery-powered, low-memory devices  
- Delay-sensitive or lossy environments  
- Frequent, small telemetry packets  

**UDPulse v1** eliminates connection setup and retransmission overhead while maintaining sufficient reliability and compact message structure.

---

## ⚙️ System Components

### 🛰 Client — `client.py`
- Initializes a UDP socket and connects to the collector.
- Sends telemetry packets containing sensor readings.
- Uses three message types: `INIT`, `DATA`, and `HEARTBEAT`.
- Maintains sequence numbers and battery level simulation.
- Configurable reporting intervals (1 s, 5 s, or 30 s).

### 🖥 Server — `server.py`
- Listens on a UDP port for incoming telemetry packets.
- Parses the 10-byte header and extracts fields.
- Logs each message to CSV with:

---

## ▶️ Run Locally

You can easily run the baseline (Phase 1) test locally using the provided **`baseline.sh`** script.

### 🧩 Prerequisites
- Python 3.8+ installed  
- Both `client.py` and `server.py` located in the same directory  
- Linux/macOS terminal or WSL on Windows  

### 🧠 Steps
 ```bash
 git clone https://github.com/karimmarwanw/IOT-Telemetry.git
 cd IOT-Telemetry
 chmod +x baseline.sh
 sudo bash baseline.sh
 ```