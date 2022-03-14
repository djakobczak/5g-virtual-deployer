#!/bin/bash

LOG_FILE="${1:-"cpu_utilization.log"}"

# read timeout 0.2 -> divide cpu usage by 5
while :
do
    echo "$(awk '{u=$2+$4; t=$2+$4+$5; if (NR==1){u1=u; t1=t;} else print ($2+$4-u1) * 20 / (t-t1) "%"; }' <(grep 'cpu ' /proc/stat) <(sleep 0.2;grep 'cpu ' /proc/stat)) $(date +%T.%3N)" >> ${LOG_FILE}
done