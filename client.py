import socket
import struct
import random
import time

INIT = 0
DATA = 1
HEARTBEAT = 2
device_id = 1
sequence_number = 0

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = '127.0.0.1'
port = 65432

header_format = '!H I I H'

def build_header(msg_type):
    global sequence_number
    sequence_number += 1
    timestamp = int(time.time())
    return struct.pack(header_format, device_id, sequence_number, timestamp, msg_type)

#INIT message
init_header = build_header(INIT)
init_payload = b"welcome to our IOT temperature sensor"
s.sendto(init_header + init_payload, (host, port))
print("INIT sent")

last_data_time = 0
last_heartbeat_time = 0
DATA_INTERVAL = 4
HEARTBEAT_INTERVAL = 1

while True:
    now = time.time()

    if now - last_data_time >= DATA_INTERVAL:
        temp = random.randint(34, 40)
        data_header = build_header(DATA)
        payload = str(temp).encode()
        s.sendto(data_header + payload, (host, port))
        print(f"sent DATA: temp={temp}")
        last_data_time = now

    if now - last_heartbeat_time >= HEARTBEAT_INTERVAL:
        heartbeat_header = build_header(HEARTBEAT)
        s.sendto(heartbeat_header, (host, port))
        print("sent HEARTBEAT")
        last_heartbeat_time = now

    time.sleep(0.1)