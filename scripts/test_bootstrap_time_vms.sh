#!/bin/bash

LOGS_PATH="${1:-"/home/djak/5gcore_measurements/vms/test-bootstrap"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"

mkdir -p ${LOGS_FULL_PATH} || exit 1
echo "$(date +"%T.%N") - Test start" > "${LOGS_FULL_PATH}/general.log"

virsh start cplane01 & >> "${LOGS_FULL_PATH}/general.log"
virsh start upf01 & >> "${LOGS_FULL_PATH}/general.log"
./test_vm_alive.sh 192.168.122.10 & > "${LOGS_FULL_PATH}/cplane_alive.log"
./test_vm_alive.sh 192.168.122.100 & > "${LOGS_FULL_PATH}/uplane_alive.log"

# wait for all jobs
for job in `jobs -p`
do
echo $job
    wait $job || echo "error: ${job}" || exit 1
done


# simple sleep for sshd
sleep 10

# gather logs
mkdir -p ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.10:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.100:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.50:/home/ops/connect-core-1ue.log ${LOGS_FULL_PATH}/gnb.log
