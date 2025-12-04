import socket
import random
import time
import struct

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

# Timers
DATA_INTERVAL = 4
HEARTBEAT_INTERVAL = 1
last_data = 0
last_hb = 0

while True:
    now = time.time()

    # Send DATA every 4 seconds
    if now - last_data >= DATA_INTERVAL:
        temp = random.randint(34, 40)
        data_header = build_header(DATA)
        client.sendto(data_header + str(temp).encode(), (HOST, PORT))
        print(f"[CLIENT] Sent DATA temp={temp}")
        last_data = now

    # Send HEARTBEAT every 1 second
    if now - last_hb >= HEARTBEAT_INTERVAL:
        hb_header = build_header(HEARTBEAT)
        client.sendto(hb_header + b"alive", (HOST, PORT))
        print("[CLIENT] Sent HEARTBEAT")
        last_hb = now

    if battery_health <= 0:
        print("[CLIENT] Battery depleted. Stopping.")
        break

    time.sleep(0.1)

client.close()