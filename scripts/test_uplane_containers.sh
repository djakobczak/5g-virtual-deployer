#!/bin/bash
set -ux

VUS="${1:-"1"}"
STRESS_DURATION="${2:-"60s"}"
CONTAINER_PROJECT_PATH="${3:-"/home/djak/docker_open5gs/"}"
LOGS_PATH="${4:-"/home/djak/5gcore_measurements/containers/test-uplane"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"
SERVER_LOGS="${LOGS_FULL_PATH}/server.log"

mkdir -p ${LOGS_FULL_PATH} || exit 1

TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
export TEST_UNIQSUFIX
STRESS_TEST_LOG="/tmp/stress-${TEST_UNIQSUFIX}.log"
MONITORING_SCRIPT="docker_stats.sh"
UE_CONFIG="ue-config-docker-1.yml"

STRESS_TEST_CMD="k6 run test_http.js --vus $VUS -d $STRESS_DURATION"
ADD_ROUTE_CMD="sudo ip route add 192.168.0.38/32 dev uesimtun0"

# source common function
source paths.sh
source common.sh

./monitoring/${MONITORING_SCRIPT} "${LOGS_FULL_PATH}/docker_stats.log" &
pushd ${CONTAINER_PROJECT_PATH}
docker-compose -f sa-deploy.yaml up -d
docker-compose -f nr-gnb.yaml up -d
sleep 10
__start_ue_bg ${UE_LOG_FILENAME} ${UE_CONFIG}
__run_on_ue_fg "${ADD_ROUTE_CMD}"
python3 -m http.server &> "${SERVER_LOGS}" &   # start http server on port 8000
sleep 5

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nVUS: ${VUS}\nSTRESS_DURATION: ${STRESS_DURATION}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"

# run stress test
__run_on_ue_fg "$STRESS_TEST_CMD" "$STRESS_TEST_LOG"
sleep 5

docker-compose -f nr-gnb.yaml logs --no-color &> "${LOGS_FULL_PATH}/gnb.log"
docker-compose logs --no-color &> "${LOGS_FULL_PATH}/core.log"
scp ops@192.168.122.60:${STRESS_TEST_LOG} ${LOGS_FULL_PATH}/stress.log

# clean up resources
__stop_ue
pkill -f "python3 -m http.server"
docker-compose -f nr-gnb.yaml stop
docker-compose stop
docker-compose -f nr-gnb.yaml rm -f
docker-compose rm -f
popd
