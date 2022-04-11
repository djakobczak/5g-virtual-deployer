#!/bin/bash
set -ux

DURATION="${1:-"20"}"
CONTAINER_PROJECT_PATH="${2:-"/home/djak/docker_open5gs/"}"
LOGS_PATH="${3:-"/home/djak/5gcore_measurements/containers/test-idle"}"
UNIQ_TEST_NAME="test-${DURATION}-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"
SERVER_LOGS="${LOGS_FULL_PATH}/server.log"

mkdir -p ${LOGS_FULL_PATH} || exit 1

TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
export TEST_UNIQSUFIX
MONITORING_SCRIPT="docker_stats.sh"

# source common functions
source paths.sh
source common.sh

trap 'kill $(jobs -p)' EXIT

./monitoring/${MONITORING_SCRIPT} "${LOGS_FULL_PATH}/docker_stats.log" &
pushd ${CONTAINER_PROJECT_PATH}
docker-compose -f sa-deploy.yaml up -d
docker-compose -f nr-gnb.yaml up -d
sleep 10

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nDURATION: ${DURATION}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"
sleep ${DURATION}
echo "$(date +"%H-%M-%S-%6N") - test ended " >> "${LOGS_FULL_PATH}/general.log"

docker system df -v &> "${LOGS_FULL_PATH}/docker_system_df.log"
docker-compose -f nr-gnb.yaml logs --no-color &> "${LOGS_FULL_PATH}/gnb.log"
docker-compose logs --no-color &> "${LOGS_FULL_PATH}/core.log"

pkill -f ${MONITORING_SCRIPT}
docker-compose -f nr-gnb.yaml down
docker-compose -f sa-deploy.yaml down
popd
