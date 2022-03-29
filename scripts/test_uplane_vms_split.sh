#!/bin/bash
set -ux

VUS="${1:-"1"}"
STRESS_DURATION="${2:-"60s"}"
LOGS_PATH="${3:-"/home/djak/5gcore_measurements/vms-split/test-uplane"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"
SERVER_LOGS="${LOGS_FULL_PATH}/server.log"

mkdir -p ${LOGS_FULL_PATH} || exit 1

TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
export TEST_UNIQSUFIX
STRESS_TEST_LOG="/tmp/stress-${TEST_UNIQSUFIX}.log"
MONITORING_MEM_SCRIPT="virsh_dommemstat.sh"

STRESS_TEST_CMD="k6 run test_http.js --vus $VUS -d $STRESS_DURATION"
ADD_ROUTE_CMD="sudo ip route add 192.168.0.38/32 dev uesimtun0"

# source common function
source paths.sh
source common.sh

echo "$(date +"%H-%M-%S-%6N") - test started " > "${LOGS_FULL_PATH}/general.log"
echo -e "Params:\nVUS: ${VUS}\nSTRESS_DURATION: ${STRESS_DURATION}\nLOGS_PATH: ${LOGS_PATH}" >> "${LOGS_FULL_PATH}/general.log"

# prepare setup
__restart_splitted_cplane
__start_gnb_bg ${GNB_LOG_FILENAME}
__start_ue_bg ${UE_LOG_FILENAME}
sleep 2
__run_on_ue_fg "${ADD_ROUTE_CMD}"
python3 -m http.server &> "${SERVER_LOGS}" &   # start http server on port 8000

# start gathering stats
./resource_monitoring.sh start ${CPU_USAGE_UPF_FILENAME} ${MEMORY_USAGE_UPF_FILENAME} ${CPU_USAGE_CPLANE_FILENAME} ${MEMORY_USAGE_CPLANE_FILENAME} ${CPU_USAGE_HOST_FILENAME}
./monitoring/${MONITORING_MEM_SCRIPT} "${LOGS_FULL_PATH}/virsh_dommenstat.log" &

sleep 10

__run_on_ue_fg "$STRESS_TEST_CMD" "$STRESS_TEST_LOG"

__stop_gnb
__stop_ue
pkill -f "python3 -m http.server"
./resource_monitoring.sh stop
pkill -f ${MONITORING_MEM_SCRIPT}

mkdir ${LOGS_FULL_PATH}/open5gs || exit 1
# gather logs
scp ops@192.168.122.10:${CPU_USAGE_CPLANE_FILENAME} ${LOGS_FULL_PATH}/cplane_cpu.log
scp ops@192.168.122.10:${MEMORY_USAGE_CPLANE_FILENAME} ${LOGS_FULL_PATH}/cplane_memory.log
scp ops@192.168.122.100:${CPU_USAGE_UPF_FILENAME} ${LOGS_FULL_PATH}/upf_cpu.log
scp ops@192.168.122.100:${MEMORY_USAGE_UPF_FILENAME} ${LOGS_FULL_PATH}/upf_memory.log
scp ops@192.168.122.60:${UE_LOG_FILENAME} ${LOGS_FULL_PATH}/ue.log
scp ops@192.168.122.60:${STRESS_TEST_LOG} ${LOGS_FULL_PATH}/stress.log
scp ops@192.168.122.50:${GNB_LOG_FILENAME} ${LOGS_FULL_PATH}/gnb.log
scp ops@192.168.122.10:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.100:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
mv ${CPU_USAGE_HOST_FILENAME} ${LOGS_FULL_PATH}/
