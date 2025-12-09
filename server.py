import socket
import struct
import time
import heapq
import csv
import os

HOST = "127.0.0.1"
PORT = 4444
SIZE = 1024

header_format = "!B B H I B B"
header_size = struct.calcsize(header_format)

message_types = {0: "INIT", 1: "DATA", 2: "HEARTBEAT"}

next_device_id = 1
device_state = {}
REORDER_WINDOW = 0.050

CSV_FILE = "telemetry_log.csv"


# ----------------------------------------------------------
# Initialize CSV file if not exists
# ----------------------------------------------------------
if not os.path.isfile(CSV_FILE):
    with open(CSV_FILE, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["device_id", "seq", "timestamp", "arrival_time", "duplicate_flag", "gap_flag"])


def format_sensor_ts(ts):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))


def format_arrival_ts(arrival):
    return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(arrival)) + f".{int((arrival % 1)*1000):03d}"


def log_to_csv(device_id, seq, ts, arrival, dup, gap):
    ts_str = format_sensor_ts(ts)
    arrival_str = format_arrival_ts(arrival)

    with open(CSV_FILE, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([device_id, seq, ts_str, arrival_str, dup, gap])


# ----------------------------------------------------------
# Device State
# ----------------------------------------------------------
def get_device_state(device_id):
    if device_id not in device_state:
        device_state[device_id] = {
            "last_seq": 0,
            "recv_count": 0,
            "dup_count": 0,
            "gap_count": 0,
            "buffer": []
        }
    return device_state[device_id]


# ----------------------------------------------------------
# ORDERED PACKET PROCESSING
# ----------------------------------------------------------
def flush_ready_packets(state, device_id, now_arrival):

    while state["buffer"]:

        ts, seq, pv, dev_id, msg_type, battery, payload, arrival = state["buffer"][0]

        if now_arrival - arrival < REORDER_WINDOW:
            break

        ts, seq, pv, dev_id, msg_type, battery, payload, arrival = heapq.heappop(state["buffer"])

        duplicate_flag = 0
        gap_flag = 0

        # ---------------- DUPLICATE DETECTION ----------------
        if seq <= state["last_seq"]:
            state["dup_count"] += 1
            duplicate_flag = 1

            print("-------------------------------------")
            print(f"[DUPLICATE] device={device_id} seq={seq} ignored (after reorder)")

            log_to_csv(device_id, seq, ts, arrival, duplicate_flag, gap_flag)
            continue

        # ---------------- GAP DETECTION ----------------
        expected = state["last_seq"] + 1
        if state["last_seq"] != 0 and seq > expected:
            missing = seq - expected
            state["gap_count"] += missing
            gap_flag = 1

            print("-------------------------------------")
            print(f"[GAP] device={device_id}: missing {missing} packets (expected {expected}, got {seq})")

        state["last_seq"] = seq

        # ---------------- FORMATTED TIMESTAMPS ----------------
        ts_str = format_sensor_ts(ts)
        arrival_str = format_arrival_ts(arrival)

        # ---------------- PRINT ORDERED PACKET ----------------
        print("-------------------------------------")
        print(f"[ORDERED] device={device_id}")
        print(f"sequence number: {seq}")
        print(f"timestamp: {ts_str} (sensor)")
        print(f"arrival:   {arrival_str} (server)")
        print(f"message type: {message_types.get(msg_type)}")
        print(f"battery: {battery}%")
        print(f"payload: {payload.decode(errors='replace')}")

        if msg_type == 1:
            print("DATA (ordered)")
        elif msg_type == 2:
            print("HEARTBEAT (ordered)")

        print(
            f"[STATE] dev={device_id} recv={state['recv_count']} "
            f"dups={state['dup_count']} gaps={state['gap_count']}"
        )

        # ---------------- LOG TO CSV ----------------
        log_to_csv(device_id, seq, ts, arrival, duplicate_flag, gap_flag)


# ----------------------------------------------------------
# START SERVER
# ----------------------------------------------------------
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
print(f"Server listening on {HOST}:{PORT}")

while True:
    message, address = server.recvfrom(SIZE)
    arrival = time.time()

    if len(message) < header_size:
        continue

    header = message[:header_size]
    payload = message[header_size:]

    pv, dev_id, seq, timestamp, msg_type, battery = struct.unpack(header_format, header)

    # ---------------- INIT HANDSHAKE ----------------
    if msg_type == 0 and dev_id == 0:
        assigned_id = next_device_id
        next_device_id += 1

        print("-------------------------------------")
        print(f"[INIT] New device from {address} → assigned device_ID = {assigned_id}")

        get_device_state(assigned_id)

        resp_header = struct.pack(
            header_format, pv, assigned_id, 0, int(time.time()), 0, 100
        )

        server.sendto(resp_header + b"ASSIGNED_ID", address)
        print(f"[SERVER] Sent assigned ID {assigned_id} to {address}")
        continue

    # ---------------- NORMAL MESSAGE ----------------
    state = get_device_state(dev_id)
    state["recv_count"] += 1

    heapq.heappush(
        state["buffer"],
        (timestamp, seq, pv, dev_id, msg_type, battery, payload, arrival)
    )

    flush_ready_packets(state, dev_id, arrival)