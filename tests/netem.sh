#!/bin/bash

IF=${1:-lo}
MODE=$2

reset() {
  sudo tc qdisc del dev "$IF" root 2>/dev/null
}

case "$MODE" in
  loss)
    echo "[NETEM] Applying 5% packet loss on $IF"
    reset
    sudo tc qdisc add dev "$IF" root netem loss 5%
    ;;
  delay)
    echo "[NETEM] Applying 100ms ±10ms delay on $IF"
    reset
    sudo tc qdisc add dev "$IF" root netem delay 100ms 10ms
    ;;
  none)
    echo "[NETEM] Removing netem from $IF"
    reset
    ;;
  *)
    echo "Usage: ./netem.sh <interface> {loss|delay|none}"
    exit 1
    ;;
esac