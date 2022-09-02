#!/bin/bash
set -ux

DURATION="${1:-"20"}"
LOGS_PATH="${2:-"/home/djak/5gcore_measurements/vms-split/test-session"}"
TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
LOGS_FULL_PATH="${LOGS_PATH}/test-${TEST_UNIQSUFIX}"

export TEST_UNIQSUFIX

# source common function
source paths.sh
source common.sh

trap 'kill $(jobs -p)' EXIT

# restart cplane services
# __virsh_core_action "start"
# sleep 20   # should take ~10s to bootstrap
__restart_splitted_cplane
sleep 15
__start_gnb_bg ${GNB_LOG_FILENAME}
sleep 2

# prepare
mkdir -p ${LOGS_FULL_PATH} || exit 1

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nDURATION: ${DURATION}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"
__start_ue_bg ${UE_LOG_FILENAME}
echo "$(date +"%H-%M-%S-%6N") - test ended " >> "${LOGS_FULL_PATH}/general.log"

sleep 4
__stop_ue
__stop_gnb
scp ops@192.168.122.60:${UE_LOG_FILENAME} ${LOGS_FULL_PATH}/ue.log
# __virsh_core_action "shutdown"
