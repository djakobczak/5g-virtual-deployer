#!/bin/bash

N_UES="${1:-"20"}"  # number of ues start in one iteration
N_ITERATIONS="${2:-"10"}"
LOGS_PATH="${3:-"/home/djak/5gcore_measurements/vms/test-connect-ues"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"

CONNECT_UES_SCRIPT="/home/ops/scripts/connect_ues.sh"
BOOTSTRAP_GNB_SCRIPT="/home/ops/scripts/bootstrap_gnb.sh"

TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
CPU_USAGE_UPF_FILENAME="/home/ops/monitoring/cpu_upf_${TEST_UNIQSUFIX}.log"
MEMORY_USAGE_UPF_FILENAME="/home/ops/monitoring/memory_upf_${TEST_UNIQSUFIX}.log"
CPU_USAGE_CPLANE_FILENAME="/home/ops/monitoring/cpu_cplane_${TEST_UNIQSUFIX}.log"
MEMORY_USAGE_CPLANE_FILENAME="/home/ops/monitoring/memory_cplane_${TEST_UNIQSUFIX}.log"
UE_LOG_FILENAME="/home/ops/logs/connect-ue-${TEST_UNIQSUFIX}.log"
GNB_LOG_FILENAME="/home/ops/gnb-${TEST_UNIQSUFIX}.log"
CPU_USAGE_HOST_FILENAME="host_virt_${TEST_UNIQSUFIX}.csv"

# prepare
mkdir -p ${LOGS_FULL_PATH} || exit 1
export TEST_UNIQSUFIX
./resource_monitoring.sh start ${CPU_USAGE_UPF_FILENAME} ${MEMORY_USAGE_UPF_FILENAME} ${CPU_USAGE_CPLANE_FILENAME} ${MEMORY_USAGE_CPLANE_FILENAME} ${CPU_USAGE_HOST_FILENAME}

# start gnb
ssh ops@192.168.122.50 "nohup sudo bash ${BOOTSTRAP_GNB_SCRIPT} &> ${GNB_LOG_FILENAME} &"
sleep 5

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nN_UES: ${N_UES}\nN_ITERATIONS: ${N_ITERATIONS}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"

# connect to ue and run bootstrap script
ssh ops@192.168.122.60 "sudo bash ${CONNECT_UES_SCRIPT} ${N_UES} ${N_ITERATIONS} ${UE_LOG_FILENAME}"
sleep 10

# stop gnb
ssh ops@192.168.122.50 "sudo pkill -f $(basename ${BOOTSTRAP_GNB_SCRIPT})"
ssh ops@192.168.122.50 "sudo pkill -f nr-gnb"

# gather logs
mkdir ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.10:${CPU_USAGE_CPLANE_FILENAME} ${LOGS_FULL_PATH}/cplane_cpu.log
scp ops@192.168.122.10:${MEMORY_USAGE_CPLANE_FILENAME} ${LOGS_FULL_PATH}/cplane_memory.log
scp ops@192.168.122.100:${CPU_USAGE_UPF_FILENAME} ${LOGS_FULL_PATH}/upf_cpu.log
scp ops@192.168.122.100:${MEMORY_USAGE_UPF_FILENAME} ${LOGS_FULL_PATH}/upf_memory.log
scp ops@192.168.122.60:${UE_LOG_FILENAME} ${LOGS_FULL_PATH}/ue.log
scp ops@192.168.122.50:${GNB_LOG_FILENAME} ${LOGS_FULL_PATH}/gnb.log
scp ops@192.168.122.10:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.100:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
mv ${CPU_USAGE_HOST_FILENAME} ${LOGS_FULL_PATH}/

# stop monitoring
./resource_monitoring.sh stop
