import socket
import random
import time

s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)  # IPv4 and UDP
host = '127.0.0.1'
port = 65432

while True:
    temp = round(random.uniform(34.0, 40.0), 2)
    message = str(temp)
    s.sendto(message.encode(), (host, port))
    print(f"Sent temperature: {message}")
    time.sleep(1)