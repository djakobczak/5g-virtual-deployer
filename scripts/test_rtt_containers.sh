#!/bin/bash
set -ux

DURATION="${1:-"60"}"
LOGS_PATH="${2:-"/home/djak/5gcore_measurements/containers/test-rtt"}"
TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
LOGS_FULL_PATH="${LOGS_PATH}/test-${TEST_UNIQSUFIX}"

UE_CONFIG="ue-config-docker-1.yml"
TUN_DEV="uesimtun0"
DEST="10.42.0.1"
ADD_ROUTE_CMD="sudo ip route add ${DEST}/32 dev ${TUN_DEV}"
PING_CMD="ping -I ${TUN_DEV} -c ${DURATION} ${DEST}"
PING_LOG="/tmp/test-ping-$(date +"%H-%M-%S-%6N").log"

export TEST_UNIQSUFIX

# source common function
source paths.sh
source common.sh

# trap 'kill $(jobs -p)' EXIT

mkdir -p ${LOGS_FULL_PATH} || exit 1

pushd ${CONTAINER_PROJECT_PATH}
docker-compose -f sa-deploy.yaml up -d
docker-compose -f nr-gnb.yaml up -d
sleep 10
__start_ue_bg "${UE_LOG_FILENAME}" "${UE_CONFIG}" "t"
sleep 1
__run_on_ue_fg "${ADD_ROUTE_CMD}"
sleep 5

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nDURATION: ${DURATION}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"
__run_on_ue_fg "${PING_CMD}" "${PING_LOG}"
echo "$(date +"%H-%M-%S-%6N") - test ended " >> "${LOGS_FULL_PATH}/general.log"
sleep 5

__stop_ue
docker-compose -f nr-gnb.yaml down
docker-compose -f sa-deploy.yaml down

scp ops@192.168.122.60:${PING_LOG} ${LOGS_FULL_PATH}/ping.log
popd
