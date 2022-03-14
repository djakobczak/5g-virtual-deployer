#!/bin/bash

N_UES="${1:-"10"}"  # number of ues start in one iteration
N_ITERATIONS="${2:-"10"}"

./resource_monitoring.sh start

# connect to ue and run bootstrap script
ssh ops@192.168.122.60 "sudo connect_ues.sh ${N_UES} ${N_ITERATIONS}"

# gather logs

# stop monitoring
./resource_monitoring.sh stop
