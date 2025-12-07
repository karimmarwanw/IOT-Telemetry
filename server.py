import socket
import struct
import time
import heapq

HOST = "127.0.0.1"
PORT = 4444
SIZE = 1024

header_format = "!B B H I B B"
header_size = struct.calcsize(header_format)

message_types = {
    0: "INIT",
    1: "DATA",
    2: "HEARTBEAT"
}

# Auto-increment device IDs
next_device_id = 1

device_state = {}

TS_WINDOW = 0.5


def get_device_state(device_id: int):
    if device_id not in device_state:
        device_state[device_id] = {
            "last_seq": 0,
            "recv_count": 0,
            "dup_count": 0,
            "gap_count": 0,
            "buffer": [],
            "newest_ts": 0,
        }
    return device_state[device_id]


def flush_ready_packets(state, device_id):

    newest_ts = state["newest_ts"]

    while state["buffer"]:
        oldest_ts = state["buffer"][0][0]  # peek earliest timestamp

        # If this packet's timestamp is not older than the window,
        # keep waiting for more packets.
        if newest_ts - oldest_ts <= TS_WINDOW:
            break

        # Pop the earliest timestamp (tie-broken by seq)
        ts, seq, payload, msg_type, arrival = heapq.heappop(state["buffer"])

        expected = state["last_seq"] + 1

        # GAP detection (true gap – earlier seq never arrived in time)
        if seq > expected and state["last_seq"] != 0:
            missing = seq - expected
            state["gap_count"] += missing
            print(
                f"[GAP] device={device_id}: missing {missing} packets "
                f"(expected {expected}, got {seq})"
            )

        # Duplicate detection (seq already flushed)
        elif seq <= state["last_seq"]:
            state["dup_count"] += 1
            print(f"[DUPLICATE] device={device_id} seq={seq} ignored (late/duplicate)")
            # Don't update last_seq or print this payload as ordered
            continue

        # Update last processed sequence
        state["last_seq"] = seq

        # Print ordered view
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        print(
            f"[ORDERED] device={device_id} seq={seq} ts={ts_str} "
            f"type={message_types.get(msg_type)} payload={payload.decode(errors='replace')}"
        )

        if msg_type == 1:
            print(f"DATA (ordered): temp={payload.decode(errors='replace')}")
        elif msg_type == 2:
            print(f"HEARTBEAT (ordered): {payload.decode(errors='replace')}")


# =========================
# SERVER MAIN LOOP
# =========================

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
print(f"Server listening on {HOST}:{PORT}")

while True:
    message, address = server.recvfrom(SIZE)
    arrival = time.time()

    header = message[:header_size]
    payload = message[header_size:]

    pv, dev_id, seq, timestamp, msg_type, battery = struct.unpack(
        header_format, header
    )

    print("-------------------------------------")
    print(f"Packet from {address}")
    print(f"protocol version: {pv}")
    print(f"device ID: {dev_id}")
    print(f"sequence number: {seq}")
    print(f"timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
    print(f"message type: {message_types.get(msg_type)}")
    print(f"battery: {battery}%")

    # =========================
    # INIT handshake
    # =========================
    if msg_type == 0 and dev_id == 0:
        assigned_id = next_device_id
        next_device_id += 1

        print(f"[SERVER] New device connected → assigned device_ID = {assigned_id}")
        get_device_state(assigned_id)

        resp_header = struct.pack(
            header_format,
            pv,            # protocol version
            assigned_id,   # new device ID
            0,             # seq for response
            int(time.time()),
            0,             # INIT
            100            # dummy battery
        )
        server.sendto(resp_header + b"ASSIGNED_ID", address)
        print(f"[SERVER] Sent assigned ID {assigned_id} to {address}")
        continue

    # =========================
    # NORMAL PACKET
    # =========================
    state = get_device_state(dev_id)
    state["recv_count"] += 1

    # Track newest sensor timestamp seen for this device
    if timestamp > state["newest_ts"]:
        state["newest_ts"] = timestamp

    # Push into timestamp-ordered heap
    heapq.heappush(state["buffer"], (timestamp, seq, payload, msg_type, arrival))

    # Try to flush any packets that are now safe to output
    flush_ready_packets(state, dev_id)

    print(
        f"[STATE] dev={dev_id} recv={state['recv_count']} "
        f"dups={state['dup_count']} gaps={state['gap_count']}"
    )