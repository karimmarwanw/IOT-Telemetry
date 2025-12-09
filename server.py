import socket
import struct
import time
import heapq

HOST = "127.0.0.1"
PORT = 4444
SIZE = 1024

# Header: version (1B), device_id (1B), seq (2B), timestamp (4B), msg_type (1B), battery (1B)
header_format = "!B B H I B B"
header_size = struct.calcsize(header_format)

message_types = {
    0: "INIT",
    1: "DATA",
    2: "HEARTBEAT",
}

# Auto-increment device IDs
next_device_id = 1

# Per-device stored state
device_state = {}

# How long to wait to allow out-of-order packets to arrive (seconds)
REORDER_WINDOW = 0.050


def get_device_state(device_id: int):
    if device_id not in device_state:
        device_state[device_id] = {
            "last_seq": 0,            # last processed (ordered) sequence
            "recv_count": 0,
            "dup_count": 0,
            "gap_count": 0,
            # Heap sorted by timestamp
            # stored as: (timestamp, seq, pv, dev_id, msg_type, battery, payload, arrival_time)
            "buffer": []
        }
    return device_state[device_id]


def flush_ready_packets(state, device_id, now_arrival):
    """
    Flush packets that have aged at least REORDER_WINDOW seconds.
    Perform gap/duplicate detection AFTER reordering.
    """
    while state["buffer"]:
        ts, seq, pv, dev_id, msg_type, battery, payload, arrival = state["buffer"][0]

        # Have we waited enough so that any earlier timestamp packet has time to arrive?
        if now_arrival - arrival < REORDER_WINDOW:
            break

        # Pop earliest timestamped packet
        ts, seq, pv, dev_id, msg_type, battery, payload, arrival = heapq.heappop(state["buffer"])

        # === ORDER-AWARE DUPLICATE DETECTION ===
        if seq <= state["last_seq"]:
            state["dup_count"] += 1
            print("-------------------------------------")
            print(f"[DUPLICATE] device={device_id} seq={seq} ignored (after reorder)")
            print(
                f"[STATE] dev={device_id} recv={state['recv_count']} "
                f"dups={state['dup_count']} gaps={state['gap_count']}"
            )
            continue

        # === ORDER-AWARE GAP DETECTION ===
        expected = state["last_seq"] + 1
        if state["last_seq"] != 0 and seq > expected:
            missing = seq - expected
            state["gap_count"] += missing
            print("-------------------------------------")
            print(
                f"[GAP] device={device_id}: missing {missing} packets "
                f"(expected {expected}, got {seq})"
            )

        # Now update the last processed sequence
        state["last_seq"] = seq

        # === PRINT ORDERED PACKET ===
        print("-------------------------------------")
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        print(f"[ORDERED] device={device_id}")
        print(f"protocol version: {pv}")
        print(f"device ID: {device_id}")
        print(f"sequence number: {seq}")
        print(f"timestamp: {ts_str} (sensor)")
        print(f"message type: {message_types.get(msg_type, 'UNKNOWN')}")
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


# ==========================
# START SERVER
# ==========================

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
print(f"Server listening on {HOST}:{PORT}")

while True:
    message, address = server.recvfrom(SIZE)
    arrival = time.time()

    if len(message) < header_size:
        print("Received too-short packet, ignoring.")
        continue

    header = message[:header_size]
    payload = message[header_size:]

    pv, dev_id, seq, timestamp, msg_type, battery = struct.unpack(header_format, header)

    # ========= INIT HANDSHAKE =========
    if msg_type == 0 and dev_id == 0:
        assigned_id = next_device_id
        next_device_id += 1

        print("-------------------------------------")
        print(f"[INIT] New device from {address} → assigned device_ID = {assigned_id}")

        # Create state entry
        get_device_state(assigned_id)

        # Send back assigned ID
        resp_header = struct.pack(
            header_format,
            pv,
            assigned_id,
            0,
            int(time.time()),
            0,      # message type INIT
            100     # dummy battery
        )
        server.sendto(resp_header + b"ASSIGNED_ID", address)
        print(f"[SERVER] Sent assigned ID {assigned_id} to {address}")
        continue

    # ========= NORMAL MESSAGES =========

    state = get_device_state(dev_id)
    state["recv_count"] += 1

    # Insert into timestamp-sorted heap
    heapq.heappush(
        state["buffer"],
        (timestamp, seq, pv, dev_id, msg_type, battery, payload, arrival)
    )

    # Reorder + detect gaps/duplicates + print
    flush_ready_packets(state, dev_id, arrival)