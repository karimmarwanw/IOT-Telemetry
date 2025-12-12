import subprocess
import time
import signal
import sys
from datetime import datetime

NETEM_SCRIPT = "./tests/netem.sh"
INTERFACE = "lo"

def run(cmd):
    return subprocess.Popen(cmd, shell=True)

def main():
    mode = sys.argv[1] if len(sys.argv) > 1 else "none"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    server_log = f"server_{mode}_{timestamp}.log"
    client_log = f"client_{mode}_{timestamp}.log"

    print(f"[+] Experiment mode: {mode}")

    # Apply netem
    subprocess.run(["sudo", NETEM_SCRIPT, INTERFACE, mode])

    # Start server
    server = run(f"python3 server.py | tee {server_log}")
    time.sleep(1)

    # Start client
    client = run(f"python3 client.py | tee {client_log}")

    try:
        time.sleep(60)  # run experiment duration
    except KeyboardInterrupt:
        pass

    print("\n[+] Stopping client and server")

    client.send_signal(signal.SIGINT)
    server.send_signal(signal.SIGINT)

    time.sleep(1)

    # Remove netem
    subprocess.run(["sudo", NETEM_SCRIPT, INTERFACE, "none"])

    print("[+] Experiment finished")
    print(f"Logs saved: {server_log}, {client_log}")

if __name__ == "__main__":
    main()