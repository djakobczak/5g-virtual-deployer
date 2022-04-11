#!/bin/bash
set -ux

DURATION="${1:-"60"}"
LOGS_PATH="${2:-"/home/djak/5gcore_measurements/vms-split/test-rtt"}"
TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
LOGS_FULL_PATH="${LOGS_PATH}/test-${TEST_UNIQSUFIX}"

TUN_DEV="uesimtun0"
DEST="10.42.0.0"
ADD_ROUTE_CMD="sudo ip route add ${DEST}/16 dev ${TUN_DEV}"
PING_CMD="ping -I ${TUN_DEV} -c ${DURATION} ${DEST}"
PING_LOG="/tmp/test-ping-$(date +"%H-%M-%S-%6N").log"

export TEST_UNIQSUFIX

# source common function
source paths.sh
source common.sh

# trap 'kill $(jobs -p)' EXIT

mkdir -p ${LOGS_FULL_PATH} || exit 1

# restart cplane services
__virsh_core_action "start"
sleep 20   # should take ~10s to bootstrap
__restart_splitted_cplane
sleep 10
__set_tuns_upf
__start_gnb_bg ${GNB_LOG_FILENAME}
sleep 2
__start_ue_bg "${UE_LOG_FILENAME}"
__run_on_ue_fg "${ADD_ROUTE_CMD}"

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nDURATION: ${DURATION}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"
__run_on_ue_fg "${PING_CMD}" "${PING_LOG}"
echo "$(date +"%H-%M-%S-%6N") - test ended " >> "${LOGS_FULL_PATH}/general.log"

sleep 5

scp ops@192.168.122.60:${PING_LOG} ${LOGS_FULL_PATH}/ping.log

__stop_gnb
__virsh_core_action "shutdown"
