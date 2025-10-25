import socket

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # IPv4 and UDP

host = "127.0.0.1"
port = 65432

s.bind((host, port))
print(f"Server is listening on {host}:{port}")

while True:
    data, address = s.recvfrom(1024)
    print(f"Received from {address}: {data.decode()}")