#!/bin/bash

# ================= CONFIG =================
MODE=${1:-none}
IFACE=lo
DURATION=60
BASE_DIR=$(pwd)
LOG_DIR="$BASE_DIR/Examples"
NETEM="$BASE_DIR/tests/netem.sh"

TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
SERVER_LOG="$LOG_DIR/server_${MODE}_${TIMESTAMP}.log"
CLIENT_LOG="$LOG_DIR/client_${MODE}_${TIMESTAMP}.log"

mkdir -p "$LOG_DIR"

# ================= CLEANUP =================
cleanup() {
    echo
    echo "[+] Cleaning up..."

    # IMPORTANT:
    # Send SIGINT so server.py executes print_final_metrics()
    [[ -n "$SERVER_PGID" ]] && kill -INT -- -"$SERVER_PGID" 2>/dev/null
    [[ -n "$CLIENT_PGID" ]] && kill -INT -- -"$CLIENT_PGID" 2>/dev/null

    # Give server time to print FINAL METRICS
    sleep 2

    # Remove netem (non-interactive sudo; never blocks)
    sudo -n "$NETEM" "$IFACE" none >/dev/null 2>&1 || true

    echo "[+] Netem removed"
}

# ================= SIGNAL HANDLING =================
trap 'cleanup; exit 0' INT TERM

# ================= START =================
echo "[+] Experiment mode: $MODE"

# Apply netem (non-interactive sudo)
sudo -n "$NETEM" "$IFACE" "$MODE"

# ================= SERVER =================
setsid bash -c "
  python3 -u server.py \
    | sed 's/^/[SERVER] /' \
    | tee \"$SERVER_LOG\"
" &
SERVER_PGID=$!

sleep 1

# ================= CLIENT =================
setsid bash -c "
  python3 -u client.py \
    | sed 's/^/[CLIENT] /' \
    | tee \"$CLIENT_LOG\"
" &
CLIENT_PGID=$!

# ================= RUN =================
sleep "$DURATION"

# ================= END =================
cleanup
exit 0