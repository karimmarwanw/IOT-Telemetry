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

next_device_id = 1
device_state = {}

# Reorder window based on SENSOR TIMESTAMP
TS_WINDOW = 0.5    # seconds – safe for jitter + delay


def get_state(dev_id):
    if dev_id not in device_state:
        device_state[dev_id] = {
            "buffer": [],          # (timestamp, seq, payload, msg_type)
            "last_seq": 0,         # last flushed sequence
            "recv": 0,
            "dups": 0,
            "gaps": 0,
            "newest_ts": 0         # newest timestamp seen for this device
        }
    return device_state[dev_id]


def flush(state, dev_id):
    """
    This is the ONLY place where:
    ✔ gaps are detected
    ✔ duplicates are detected
    ✔ ordered packets are printed
    """

    while state["buffer"]:
        oldest_ts = state["buffer"][0][0]
        newest_ts = state["newest_ts"]

        # Wait until we are SURE no earlier packet can still arrive
        if newest_ts - oldest_ts <= TS_WINDOW:
            break

        # Pop in true timestamp order
        ts, seq, payload, msg_type = heapq.heappop(state["buffer"])
        expected = state["last_seq"] + 1

        # GAP detection (correct)
        if seq > expected and state["last_seq"] != 0:
            missing = seq - expected
            state["gaps"] += missing
            print(f"[GAP] device={dev_id}: missing {missing} packets "
                  f"(expected {expected}, got {seq})")

        # DUP detection (correct)
        elif seq <= state["last_seq"]:
            state["dups"] += 1
            print(f"[DUPLICATE] device={dev_id} seq={seq} ignored (late)")
            continue

        # Advance sequence
        state["last_seq"] = seq

        # Print ordered output
        formatted_ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(ts))
        print(f"[ORDERED] device={dev_id} seq={seq} ts={formatted_ts} "
              f"type={message_types[msg_type]} payload={payload.decode()}")

        if msg_type == 1:
            print(f"DATA (ordered): {payload.decode()}")
        elif msg_type == 2:
            print(f"HEARTBEAT (ordered): {payload.decode()}")


# Start server
server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))
print(f"Server listening on {HOST}:{PORT}")

while True:
    msg, addr = server.recvfrom(SIZE)
    header = msg[:header_size]
    payload = msg[header_size:]

    pv, dev_id, seq, ts, msg_type, batt = struct.unpack(header_format, header)

    print("-------------------------------------")
    print(f"Packet from {addr}")
    print(f"seq={seq}, ts={time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(ts))}, type={message_types[msg_type]}")

    # ---- INIT ----
    if msg_type == 0 and dev_id == 0:
        assigned = next_device_id
        next_device_id += 1

        print(f"[SERVER] Assigning new device ID: {assigned}")

        response = struct.pack(
            header_format,
            pv, assigned, 0, int(time.time()), 0, 100
        )
        server.sendto(response + b"ASSIGNED_ID", addr)
        get_state(assigned)
        continue

    # ---- NORMAL PACKET ----
    state = get_state(dev_id)
    state["recv"] += 1

    # Update newest sensor timestamp seen
    state["newest_ts"] = max(state["newest_ts"], ts)

    # Push packet into timestamp-ordered buffer
    heapq.heappush(state["buffer"], (ts, seq, payload, msg_type))

    # Attempt to flush reordering buffer
    flush(state, dev_id)

    print(f"[STATE] recv={state['recv']} dups={state['dups']} gaps={state['gaps']}")