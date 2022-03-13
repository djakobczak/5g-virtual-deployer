#!/bin/bash
set -u

IP="${1:-192.168.122.10}"
TIMEOUT="0.1"

SUCCESS=1
echo "$(date +"%T.%6N") start waiting for vm"
while :
do
    echo $(date +"%T.%6N - $IP - try to connect...")
    timeout ${TIMEOUT} ping -c 1 -n ${IP} &> /dev/null && SUCCESS=0
    [[ "$SUCCESS" == "0" ]] && echo "$(date +"%T.%6N") - ${IP} - ping successful" && exit 0
done
