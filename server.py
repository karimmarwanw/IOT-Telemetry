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

# Per-device state
device_state = {}

# Time-based reordering window (seconds)
REORDER_WINDOW = 0.050


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


def flush_ready_packets(state, device_id, now_arrival):

    while state["buffer"]:
        ts, seq, payload, msg_type, arrival = state["buffer"][0]
        if now_arrival - arrival < REORDER_WINDOW:
            break

        ts, seq, payload, msg_type, arrival = heapq.heappop(state["buffer"])
        ts_str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))

        print(f"[ORDERED] device={device_id} seq={seq} ts={ts_str} "
              f"type={message_types.get(msg_type)} payload={payload.decode(errors='replace')}")

        if msg_type == 1:
            print(f"DATA (ordered): temp={payload.decode(errors='replace')}")
        elif msg_type == 2:
            print(f"HEARTBEAT (ordered): {payload.decode(errors='replace')}")


# Start server
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
print(f"Server listening on {HOST}:{PORT}")

while True:
    message, address = server.recvfrom(SIZE)
    arrival = time.time()

    header = message[:header_size]
    payload = message[header_size:]

    pv, dev_id, seq, timestamp, msg_type, battery = struct.unpack(header_format, header)

    print("-------------------------------------")
    print(f"Packet from {address}")
    print(f"protocol version: {pv}")
    print(f"device ID: {dev_id}")
    print(f"sequence number: {seq}")
    print(f"timestamp: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))}")
    print(f"message type: {message_types.get(msg_type)}")
    print(f"battery: {battery}%")

    # INIT handshake
    if msg_type == 0 and dev_id == 0:
        assigned_id = next_device_id
        next_device_id += 1

        print(f"[SERVER] New device connected → assigned device_ID = {assigned_id}")
        get_device_state(assigned_id)

        resp_header = struct.pack(
            header_format,
            pv,             # same protocol version
            assigned_id,    # new device ID
            0,              # seq for response
            int(time.time()),
            0,              # INIT type
            100             # dummy battery
        )

        server.sendto(resp_header + b"ASSIGNED_ID", address)
        print(f"[SERVER] Sent assigned ID {assigned_id} to {address}")
        continue

    # Normal message
    state = get_device_state(dev_id)
    state["recv_count"] += 1

    # Duplicate suppression
    if seq <= state["last_seq"]:
        state["dup_count"] += 1
        print(f"[DUPLICATE] device={dev_id} seq={seq} ignored")
        print(f"[STATE] dev={dev_id} recv={state['recv_count']} "
              f"dups={state['dup_count']} gaps={state['gap_count']}")
        continue

    # Gap detection
    expected = state["last_seq"] + 1
    if seq > expected and state["last_seq"] != 0:
        missing = seq - expected
        state["gap_count"] += missing
        print(f"[GAP] device={dev_id}: missing {missing} packets "
              f"(expected {expected}, got {seq})")

    state["last_seq"] = seq

    heapq.heappush(state["buffer"], (timestamp, seq, payload, msg_type, arrival))
    flush_ready_packets(state, dev_id, arrival)
    print(f"[STATE] recv={state['recv_count']} "
          f"dups={state['dup_count']} gaps={state['gap_count']}")