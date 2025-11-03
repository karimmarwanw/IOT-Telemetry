#!/bin/bash

DURATION=60

echo "Starting server..."
python3 server.py &
SERVER_PID=$!
sleep 1

echo "Starting client..."
python3 client.py &
CLIENT_PID=$!

echo "Running baseline test for $DURATION seconds..."
sleep $DURATION

echo "Stopping processes..."
kill $CLIENT_PID 2>/dev/null
kill $SERVER_PID 2>/dev/null

echo "Baseline test finished." 
