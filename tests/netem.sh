{\rtf1\ansi\ansicpg1252\cocoartf2865
\cocoatextscaling0\cocoaplatform0{\fonttbl\f0\fswiss\fcharset0 Helvetica;}
{\colortbl;\red255\green255\blue255;}
{\*\expandedcolortbl;;}
\paperw11900\paperh16840\margl1440\margr1440\vieww11520\viewh8400\viewkind0
\pard\tx720\tx1440\tx2160\tx2880\tx3600\tx4320\tx5040\tx5760\tx6480\tx7200\tx7920\tx8640\pardirnatural\partightenfactor0

\f0\fs24 \cf0 #!/bin/bash\
\
IF=$\{1:-lo\}\
MODE=$2\
\
reset() \{\
  sudo tc qdisc del dev $IF root 2>/dev/null\
\}\
\
case "$MODE" in\
  loss)\
    echo "[NETEM] Applying 5% packet loss on $IF"\
    reset\
    sudo tc qdisc add dev $IF root netem loss 5%\
    ;;\
  delay)\
    echo "[NETEM] Applying 100ms \'b110ms delay on $IF"\
    reset\
    sudo tc qdisc add dev $IF root netem delay 100ms 10ms\
    ;;\
  none)\
    echo "[NETEM] Removing netem from $IF"\
    reset\
    ;;\
  *)\
    echo "Usage: ./netem.sh <interface> \{loss|delay|none\}"\
    exit 1\
    ;;\
esac}