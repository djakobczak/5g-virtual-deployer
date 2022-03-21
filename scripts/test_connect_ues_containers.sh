#!/bin/bash
set -ux

N_UES="${1:-"20"}"  # number of ues start in one iteration
N_ITERATIONS="${2:-"20"}"
CONTAINER_PROJECT_PATH="${3:-"/home/djak/docker_open5gs/"}"
TIMEOUT="${4:-"5"}"
LOGS_PATH="${5:-"/home/djak/5gcore_measurements/containers/test-connect-ues"}"

UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
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

./monitoring/${MONITORING_SCRIPT} "${LOGS_FULL_PATH}/docker_stats.log" &

pushd ${CONTAINER_PROJECT_PATH}

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nN_UES: ${N_UES}\nN_ITERATIONS: ${N_ITERATIONS}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"

docker-compose -f sa-deploy.yaml up -d
docker-compose -f nr-gnb.yaml up -d
sleep 8

# start ues
# set -a
# source .env
# export NR_NUMBER_UES="${N_UES}"  # number of ues per ue container
# N_ITERATIONS="$((10+${N_ITERATIONS}))"
# UE_NUM="1"

ssh ops@192.168.122.60 "sudo bash ${CONNECT_UES_SCRIPT} ${N_UES} ${N_ITERATIONS} ${UE_LOG_FILENAME} ${UE_TEMPLATE_PATH}"

# for ueIpSuf in $(seq 10 ${N_ITERATIONS}); do
#   export NR_UE_IP="172.22.0.1${ueIpSuf}"
#   IMSI="00101$(printf %010d ${UE_NUM})"

#   sed -i "s/UE1_IMSI.*/UE1_IMSI=${IMSI}/g" .env
#   echo "$(date +"%H-%M-%S-%6N") - start ue-${ueIpSuf} " >> "${LOGS_FULL_PATH}/general.log"
#   timeout ${TIMEOUT} docker-compose -p "ue-${ueIpSuf}" -f nr-ue.yaml up &> "${UES_LOGS}/ue-${ueIpSuf}.log" &
#   sleep 1

#   docker-compose -p "ue-${ueIpSuf}" -f nr-ue.yaml --no-color &>> "${UES_LOGS}/ue-${ueIpSuf}.log" &
#   UE_NUM=$(($UE_NUM + $N_UES))
# done

sleep 10
docker-compose -f nr-gnb.yaml logs --no-color &> "${UES_LOGS}/gnb.log"
docker-compose logs --no-color &> "${UES_LOGS}/core.log"

pkill -f ${MONITORING_SCRIPT}
docker-compose -f nr-gnb.yaml down
docker-compose -f sa-deploy.yaml down
scp ops@192.168.122.60:${UE_LOG_FILENAME} ${LOGS_FULL_PATH}/ue.log

docker rm $(docker ps -qa)
popd
