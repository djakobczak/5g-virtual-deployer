#!/bin/bash
set -ux

DURATION="${1:-"20"}"
LOGS_PATH="${2:-"/home/djak/5gcore_measurements/vms-split/test-idle"}"
TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
LOGS_FULL_PATH="${LOGS_PATH}/test-${TEST_UNIQSUFIX}"
MONITORING_MEM_SCRIPT="virsh_dommemstat.sh"

export TEST_UNIQSUFIX

# source common function
source paths.sh
source common.sh

trap 'kill $(jobs -p)' EXIT

# restart cplane services
__virsh_core_action "start"
sleep 20   # should take ~10s to bootstrap
__restart_splitted_cplane
sleep 10
__start_gnb_bg ${GNB_LOG_FILENAME}

# prepare
mkdir -p ${LOGS_FULL_PATH} || exit 1
./resource_monitoring.sh "start-min" ${CPU_USAGE_UPF_FILENAME} ${MEMORY_USAGE_UPF_FILENAME} ${CPU_USAGE_CPLANE_FILENAME} ${MEMORY_USAGE_CPLANE_FILENAME} ${CPU_USAGE_HOST_FILENAME}
./monitoring/${MONITORING_MEM_SCRIPT} "${LOGS_FULL_PATH}/virsh_dommenstat.log" &
sleep 5

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nDURATION: ${DURATION}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"
sleep $DURATION
echo "$(date +"%H-%M-%S-%6N") - test ended " >> "${LOGS_FULL_PATH}/general.log"

sleep 5

./resource_monitoring.sh stop
__stop_gnb
__virsh_core_action "shutdown"

mv ${CPU_USAGE_HOST_FILENAME} ${LOGS_FULL_PATH}/

pkill -f ${MONITORING_MEM_SCRIPT}
