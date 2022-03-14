#!/bin/bash

N_UES="${1:-"20"}"  # number of ues start in one iteration
N_ITERATIONS="${2:-"10"}"
LOGS_PATH="${3:-"/home/djak/5gcore_measurements/vms/test-connect-ues"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"

CONNECT_UES_SCRIPT="/home/ops/scripts/connect_ues.sh"

mkdir -p ${LOGS_FULL_PATH} || exit 1

TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
CPU_USAGE_UPF_FILENAME="/home/ops/monitoring/cpu_upf_${TEST_UNIQSUFIX}.log"
CPU_USAGE_CPLANE_FILENAME="/home/ops/monitoring/cplane_upf_${TEST_UNIQSUFIX}.log"
CPU_USAGE_HOST_FILENAME="host_virt_${TEST_UNIQSUFIX}.csv"

./resource_monitoring.sh start ${CPU_USAGE_UPF_FILENAME} ${CPU_USAGE_CPLANE_FILENAME} ${CPU_USAGE_HOST_FILENAME}

# connect to ue and run bootstrap script
ssh ops@192.168.122.60 "sudo bash ${CONNECT_UES_SCRIPT} ${N_UES} ${N_ITERATIONS}"

# gather logs
scp ops@192.168.122.10:${CPU_USAGE_CPLANE_FILENAME} ${LOGS_FULL_PATH}/cplane_cpu.log
scp ops@192.168.122.100:${CPU_USAGE_UPF_FILENAME} ${LOGS_FULL_PATH}/upf_cpu.log
mv ${CPU_USAGE_HOST_FILENAME} ${LOGS_FULL_PATH}/

# stop monitoring
./resource_monitoring.sh stop
