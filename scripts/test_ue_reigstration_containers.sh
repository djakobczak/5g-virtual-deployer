#!/bin/bash
set -ux

LOGS_PATH="${1:-"/home/djak/5gcore_measurements/containers/test-session-v2"}"
CONTAINER_PROJECT_PATH="${2:-"/home/djak/docker_open5gs/"}"
TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
LOGS_FULL_PATH="${LOGS_PATH}/test-${TEST_UNIQSUFIX}"
UE_CONFIG="ue-config-docker-1.yml"

export TEST_UNIQSUFIX

# source common function
source paths.sh
source common.sh

trap 'kill $(jobs -p)' EXIT

pushd ${CONTAINER_PROJECT_PATH}
docker-compose -f sa-deploy.yaml up -d
sleep 7
docker-compose -f nr-gnb.yaml up -d
sleep 3

# prepare
mkdir -p ${LOGS_FULL_PATH} || exit 1

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"
# __start_ue_bg ${UE_LOG_FILENAME} "${UE_CONFIG}" "t"
docker-compose -f nr-ue.yaml up -d
echo "$(date +"%H-%M-%S-%6N") - test ended " >> "${LOGS_FULL_PATH}/general.log"

sleep 3
docker-compose -f nr-ue.yaml logs --no-color &> "${LOGS_FULL_PATH}/ue.log"
docker-compose -f nr-gnb.yaml logs --no-color &> "${LOGS_FULL_PATH}/gnb.log"
docker-compose -f sa-deploy.yaml logs --no-color &> "${LOGS_FULL_PATH}/sa-deploy.log"

# scp ops@192.168.122.60:${UE_LOG_FILENAME} ${LOGS_FULL_PATH}/ue.log

# __stop_ue
docker-compose -f nr-ue.yaml down -t1
docker-compose -f nr-gnb.yaml down -t1
docker-compose -f sa-deploy.yaml down -t1
docker-compose -f nr-ue.yaml rm -f
docker-compose -f nr-gnb.yaml rm -f
docker-compose -f sa-deploy.yaml rm -f
popd
