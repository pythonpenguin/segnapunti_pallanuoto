#!/bin/bash
# Diagnostico connessione Wi-Fi verso Raspberry hotspot

# Cambia se la tua interfaccia è diversa
IFACE="wlp0s20f3"
TARGET="192.168.50.1"   # IP della Raspberry (hotspot)

echo "📡 Monitoraggio connessione Wi-Fi ($IFACE) verso $TARGET"
echo "Premi CTRL+C per interrompere."
echo "-----------------------------------------"

while true; do
    # livello del segnale
    RSSI=$(iwconfig $IFACE 2>/dev/null | grep -i --color=never "Signal level" | awk -F'=' '{print $3}' | awk '{print $1}')

    # qualità link
    QUALITY=$(iwconfig $IFACE 2>/dev/null | grep -i "Link Quality" | awk -F'=' '{print $2}' | awk '{print $1}')

    # ping singolo alla Raspberry
    PING=$(ping -c 1 -W 1 $TARGET 2>/dev/null | grep "time=" | awk -F'time=' '{print $2}' | awk '{print $1}')

    # se il ping fallisce
    if [ -z "$PING" ]; then
        PING="timeout"
    fi

    DATE=$(date +"%H:%M:%S")
    echo "$DATE | RSSI: ${RSSI} dBm | Quality: ${QUALITY} | Ping: ${PING} ms"
    sleep 1
done
