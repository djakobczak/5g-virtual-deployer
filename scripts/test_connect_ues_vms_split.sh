#!/bin/bash

N_UES="${1:-"10"}"  # number of ues start in one iteration
N_ITERATIONS="${2:-"40"}"
LOGS_PATH="${3:-"/home/djak/5gcore_measurements/vms-split/test-connect-ues"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"

CONNECT_UES_SCRIPT="/home/ops/scripts/connect_ues.sh"
MONITORING_MEM_SCRIPT="virsh_dommemstat.sh"

TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
export TEST_UNIQSUFIX

# source common function
source paths.sh
source common.sh

# prepare
mkdir -p ${LOGS_FULL_PATH} || exit 1
./resource_monitoring.sh start ${CPU_USAGE_UPF_FILENAME} ${MEMORY_USAGE_UPF_FILENAME} ${CPU_USAGE_CPLANE_FILENAME} ${MEMORY_USAGE_CPLANE_FILENAME} ${CPU_USAGE_HOST_FILENAME}
./monitoring/${MONITORING_MEM_SCRIPT} "${LOGS_FULL_PATH}/virsh_dommenstat.log" &

# restart cplane services
__restart_splitted_cplane

# start gnb
__start_gnb_bg ${GNB_LOG_FILENAME}
sleep 10

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nN_UES: ${N_UES}\nN_ITERATIONS: ${N_ITERATIONS}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"

# connect to ue and run bootstrap script
ssh ops@192.168.122.60 "sudo bash ${CONNECT_UES_SCRIPT} ${N_UES} ${N_ITERATIONS} ${UE_LOG_FILENAME}"
sleep 10

# stop gnb
__stop_gnb

# gather logs
mkdir ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.10:${CPU_USAGE_CPLANE_FILENAME} ${LOGS_FULL_PATH}/amf_cpu.log
scp ops@192.168.122.10:${MEMORY_USAGE_CPLANE_FILENAME} ${LOGS_FULL_PATH}/amf_memory.log
scp ops@192.168.122.100:${CPU_USAGE_UPF_FILENAME} ${LOGS_FULL_PATH}/upf_cpu.log
scp ops@192.168.122.100:${MEMORY_USAGE_UPF_FILENAME} ${LOGS_FULL_PATH}/upf_memory.log
scp ops@192.168.122.60:${UE_LOG_FILENAME} ${LOGS_FULL_PATH}/ue.log
scp ops@192.168.122.50:${GNB_LOG_FILENAME} ${LOGS_FULL_PATH}/gnb.log
scp ops@192.168.122.10:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.11:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.12:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.13:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.14:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.16:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.18:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.19:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.20:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.100:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
mv ${CPU_USAGE_HOST_FILENAME} ${LOGS_FULL_PATH}/

# stop monitoring
./resource_monitoring.sh stop
pkill -f ${MONITORING_MEM_SCRIPT}
