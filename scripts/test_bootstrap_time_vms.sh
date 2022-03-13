#!/bin/bash

LOGS_PATH="${1:-"/home/djak/5gcore_measurements/vms/test-bootstrap"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"

mkdir -p ${LOGS_FULL_PATH} || exit 1

# start gnb process
ssh ops@192.168.122.50 "nohup sudo bash -c scripts/bootstrap_gnb.sh &> /tmp/connect-core-1ue.log &"

source /home/djak/.cache/pypoetry/virtualenvs/cloud-init-configs-SQ1gaKbt-py3.8/bin/activate
pushd /home/djak/5gcore-vms
export PYTHONPATH=.

echo "$(date +"%T.%N") - Test start" > "${LOGS_FULL_PATH}/general.log"
python3 fgcore_runner/cli.py setup create --vm upf01-min-rdy --vm cplane01-min-rdy --skip-copy &
popd
./test_host_alive.sh 192.168.122.10 > "${LOGS_FULL_PATH}/cplane_alive.log" &
./test_host_alive.sh 192.168.122.100 > "${LOGS_FULL_PATH}/uplane_alive.log" &

# wait for all jobs
for job in `jobs -p`
do
echo $job
    wait $job || echo "error: ${job}" || exit 1
done


# simple sleep for sshd
sleep 15

# gather logs
mkdir -p ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.10:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.100:/open5gs/install/var/log/open5gs/* ${LOGS_FULL_PATH}/open5gs
scp ops@192.168.122.50:/tmp/connect-core-1ue.log ${LOGS_FULL_PATH}/gnb.log

# stop gnb process
ssh ops@192.168.122.50 "sudo pkill -f bootstrap_gnb.sh"
ssh ops@192.168.122.50 "sudo pkill -f nr-gnb"

pushd /home/djak/5gcore-vms
python3 fgcore_runner/cli.py setup remove --vm upf01-min-rdy --vm cplane01-min-rdy
deactivate
