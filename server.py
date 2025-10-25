import socket
import struct
import time

header_format = '!H I I H'
header_size = struct.calcsize(header_format)

message_types = {
    0: "INIT",
    1: "DATA",
    2: "HEARTBEAT"
}

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
host = "127.0.0.1"
port = 65432
s.bind((host, port))

print(f"Server is listening on {host}:{port}")

while True:
    data, address = s.recvfrom(1024)

    header = data[:header_size] # make that first 12 bytes are the header bytes
    payload = data[header_size:] # and rest are payload

    device_id, seq, timestamp, msg_type = struct.unpack(header_format, header)
    msg_name = message_types.get(msg_type, "undefined") # if message type in message_types ok else undefined

    ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

    print(f"packet from {address}")
    print(f"device ID: {device_id}")
    print(f"sequence number: {seq}")
    print(f"timestamp: {ts_str}")
    print(f"message Type: {msg_name}")

    if msg_name == "DATA":
        print(f"temperature: {payload.decode()}")
    elif msg_name == "HEARTBEAT":
        print("this is a heartbeat payload")
    elif msg_name == "INIT":
        print(f"payload: {payload.decode()}")
    print("-------------------------------------")