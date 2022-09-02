#!/bin/bash
set -ux

N_UES="${1:-"30"}"  # number of ues start in one iteration
N_ITERATIONS="${2:-"30"}"
CONTAINER_PROJECT_PATH="${3:-"/home/djak/docker_open5gs/"}"
TIMEOUT="${4:-"5"}"
LOGS_PATH="${5:-"/home/djak/5gcore_measurements/containers/test-connect-ues"}"

UNIQ_TEST_NAME="test-${N_UES}-${N_ITERATIONS}-$(date +"%H-%M-%S-%6N")"
UE_LOG_FILENAME="/home/ops/logs/connect-ue-${UNIQ_TEST_NAME}.log"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"
UES_LOGS="${LOGS_FULL_PATH}/ues"
UE_TEMPLATE_PATH="/home/ops/nf_configs/ue-template_docker.yml"

MONITORING_SCRIPT="docker_stats.sh"
CONNECT_UES_SCRIPT="/home/ops/scripts/connect_ues.sh"

if [[ ! -d "${CONTAINER_PROJECT_PATH}" ]]; then
  echo "Project path (${CONTAINER_PROJECT_PATH}) does not exist, exit..."
  exit 1
fi

mkdir -p ${UES_LOGS} || exit 1

trap 'kill $(jobs -p)' EXIT

pushd ${CONTAINER_PROJECT_PATH}
docker-compose -f sa-deploy.yaml up -d
docker-compose -f nr-gnb.yaml up -d
sleep 15
popd
./monitoring/${MONITORING_SCRIPT} "${LOGS_FULL_PATH}/docker_stats.log" &
pushd ${CONTAINER_PROJECT_PATH}
sleep 6

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nN_UES: ${N_UES}\nN_ITERATIONS: ${N_ITERATIONS}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"
ssh ops@192.168.122.60 "sudo bash ${CONNECT_UES_SCRIPT} ${N_UES} ${N_ITERATIONS} ${UE_LOG_FILENAME} ${UE_TEMPLATE_PATH}"
echo "$(date +"%H-%M-%S-%6N") - test ended " >> "${LOGS_FULL_PATH}/general.log"

sleep 10
docker-compose -f nr-gnb.yaml logs --no-color &> "${UES_LOGS}/gnb.log"
docker-compose logs --no-color &> "${UES_LOGS}/core.log"

pkill -f ${MONITORING_SCRIPT}
docker-compose -f nr-gnb.yaml down
docker-compose -f sa-deploy.yaml down
scp ops@192.168.122.60:${UE_LOG_FILENAME} ${LOGS_FULL_PATH}/ue.log

docker rm $(docker ps -qa)
popd
