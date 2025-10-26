import socket
import struct
import random
import time

INIT = 0
DATA = 1
HEARTBEAT = 2
protocol_version = 1
device_id = 1
sequence_number = 0

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = '127.0.0.1'
port = 65432

header_format = '!B B H I B' # protocol_version, device_id, sequence_number, timestamp, msg_type

def build_header(msg_type):
    global sequence_number
    sequence_number += 1
    timestamp = int(time.time())
    return struct.pack(header_format, protocol_version, device_id, sequence_number, timestamp, msg_type)

#INIT message
message = "welcome to our IOT temperature sensor"
init_payload = message.encode()
init_header = build_header(INIT)
s.sendto(init_header + init_payload, (host, port))
print("INIT sent")

last_data_time = 0
last_heartbeat_time = 0
DATA_INTERVAL = 4
HEARTBEAT_INTERVAL = 1

while True:
    now = time.time()

    # Data message
    if now - last_data_time >= DATA_INTERVAL:
        temp = random.randint(34, 40)
        data_payload = str(temp).encode()
        data_header = build_header(DATA)
        s.sendto(data_header + data_payload, (host, port))
        print(f"sent DATA: temp={temp}")
        last_data_time = now

    # Heartbeat message
    if now - last_heartbeat_time >= HEARTBEAT_INTERVAL:
        message = "the sensor is still alive"
        heartbeat_payload = message.encode()
        heartbeat_header = build_header(HEARTBEAT)
        s.sendto(heartbeat_header + heartbeat_payload, (host, port))
        print("sent HEARTBEAT")
        last_heartbeat_time = now

    time.sleep(0.1)