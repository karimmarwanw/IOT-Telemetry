import socket
import struct
import time

HOST = '127.0.0.1'
PORT = 4444
SIZE = 1024

header_format = '!B B H I B B'
header_size = struct.calcsize(header_format)

message_types = {
    0: "INIT",
    1: "DATA",
    2: "HEARTBEAT"
}

server = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
server.bind((HOST, PORT))

print(f"Server listening on {HOST}:{PORT}")

while True:
    message, address = server.recvfrom(SIZE)

    header_bytes = message[:header_size]
    payload_bytes = message[header_size:]

    protocol_version, device_ID, sequence_number, timestamp, message_type, battery_health = struct.unpack(header_format, header_bytes)

    ts_str = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(timestamp))

    print(f"packet from: {address}")
    print(f"protocol version: {protocol_version}")
    print(f"device ID: {device_ID}")
    print(f"sequence number: {sequence_number}")
    print(f"timestamp: {ts_str}")
    print(f"message Type: {message_types.get(message_type, 'undefined')}")
    print(f"battery health: {battery_health}%")

    if message_type == 0:  # INIT
        print(f"payload: {payload_bytes.decode()}")
    elif message_type == 1:  # DATA
        print(f"temperature: {payload_bytes.decode()}")
    elif message_type == 2:  # HEARTBEAT
        print(f"payload: {payload_bytes.decode()}")

    print("-------------------------------------")