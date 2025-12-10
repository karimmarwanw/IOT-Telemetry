import socket
import random
import time
import struct
import argparse

HOST = "127.0.0.1"
PORT = 4444

# Message types
INIT = 0
DATA = 1
HEARTBEAT = 2

# Initial temporary device ID (server will assign real one)
device_ID = 0

# Protocol fields
protocol_version = 1
sequence_number = 0
battery_health = 100

protocol_header = "!B B H I B B"


# ----------------------------------------------------------
# Argument parser for batching + intervals
# ----------------------------------------------------------
parser = argparse.ArgumentParser()

parser.add_argument(
    "-b", "--batch", type=int, default=1,
    help="Batch size (how many readings per DATA packet). Default = 1"
)

parser.add_argument(
    "-d", "--data_interval", type=float, default=4,
    help="Interval (seconds) between DATA readings. Default = 4"
)

parser.add_argument(
    "-H", "--heartbeat_interval", type=float, default=1,
    help="Interval (seconds) between HEARTBEAT packets. Default = 1"
)

args = parser.parse_args()

BATCH_SIZE = max(1, args.batch)
DATA_INTERVAL = max(0.1, args.data_interval)
HEARTBEAT_INTERVAL = max(0.1, args.heartbeat_interval)

batch_buffer = []


# ----------------------------------------------------------
# Header builder
# ----------------------------------------------------------
def build_header(msg_type):
    global sequence_number, battery_health

    sequence_number += 1
    timestamp = int(time.time())

    if sequence_number % 5 == 0:
        battery_health -= 1

    return struct.pack(
        protocol_header,
        protocol_version,
        device_ID,
        sequence_number,
        timestamp,
        msg_type,
        battery_health
    )


# ----------------------------------------------------------
# Client socket
# ----------------------------------------------------------
client = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# INIT handshake
init_msg = b"client booting"
init_header = build_header(INIT)
client.sendto(init_header + init_msg, (HOST, PORT))
print("[CLIENT] Sent INIT with device_ID = 0")

resp, addr = client.recvfrom(1024)
resp_header = resp[:struct.calcsize(protocol_header)]
pv, assigned_id, _, _, _, _ = struct.unpack(protocol_header, resp_header)

device_ID = assigned_id
print(f"[CLIENT] Assigned device ID = {device_ID}")

print(f"[CLIENT] Configuration:")
print(f"  Batch size          = {BATCH_SIZE}")
print(f"  DATA interval       = {DATA_INTERVAL} seconds")
print(f"  HEARTBEAT interval  = {HEARTBEAT_INTERVAL} seconds")


# ----------------------------------------------------------
# Timers
# ----------------------------------------------------------
last_data = 0
last_hb = 0


# ----------------------------------------------------------
# Main Loop
# ----------------------------------------------------------
while True:
    now = time.time()

    # Add a reading every DATA_INTERVAL seconds
    if now - last_data >= DATA_INTERVAL:
        temp = random.randint(34, 40)
        batch_buffer.append(temp)
        print(f"[CLIENT] Added reading: {temp}  | Batch = {batch_buffer}")
        last_data = now

        # If batching off (size = 1) send immediately
        if BATCH_SIZE == 1:
            header = build_header(DATA)
            client.sendto(header + str(temp).encode(), (HOST, PORT))
            print(f"[CLIENT] Sent DATA temp={temp}")
            batch_buffer.clear()

    # If batch is full, send all readings
    if len(batch_buffer) >= BATCH_SIZE:
        header = build_header(DATA)
        payload = ",".join(str(x) for x in batch_buffer).encode()
        client.sendto(header + payload, (HOST, PORT))

        print(f"[CLIENT] Sent BATCHED DATA ({len(batch_buffer)} readings): {batch_buffer}")
        batch_buffer.clear()

    # Send HEARTBEAT packets on interval
    if now - last_hb >= HEARTBEAT_INTERVAL:
        hb_header = build_header(HEARTBEAT)
        client.sendto(hb_header + b"alive", (HOST, PORT))
        print("[CLIENT] Sent HEARTBEAT")
        last_hb = now

    # Stop when battery is empty
    if battery_health <= 0:
        print("[CLIENT] Battery depleted. Stopping.")
        break

    time.sleep(0.05)

client.close()