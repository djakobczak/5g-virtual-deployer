#!/bin/bash

LOGS_PATH="${1:-"/home/djak/5gcore_measurements/containers/test-bootstrap"}"
CONTAINER_PROJECT_PATH="${2:-"/home/djak/docker_open5gs/"}"
UNIQ_TEST_NAME="test-$(date +"%H-%M-%S-%6N")"
LOGS_FULL_PATH="${LOGS_PATH}/${UNIQ_TEST_NAME}"

if [[ ! -d "${CONTAINER_PROJECT_PATH}" ]]; then
  echo "Project path (${CONTAINER_PROJECT_PATH}) does not exist, exit..."
  exit 1
fi

mkdir -p ${LOGS_FULL_PATH} || exit 1
./test_host_alive.sh 172.22.0.10 > "${LOGS_FULL_PATH}/cplane_alive.log" &  # amf
./test_host_alive.sh 172.22.0.8 > "${LOGS_FULL_PATH}/uplane_alive.log" &

pushd $CONTAINER_PROJECT_PATH
# start gnb container
docker-compose -f sa-deploy.yaml up -d smf ausf bsf nrf nssf pcf udm udr mongo &
sleep 7

docker-compose -f nr-gnb.yaml up -d
echo "$(date +"%T.%N") - Test start" > "${LOGS_FULL_PATH}/general.log"
docker-compose -f sa-deploy.yaml up -d amf upf
while true;
do
  sleep 0.2
  docker-compose -f nr-gnb.yaml logs --no-color > "${LOGS_FULL_PATH}/gnb.log"
  echo "$(date +"%T.%N")"
  cat "${LOGS_FULL_PATH}/gnb.log"
  if grep -q "successful" "${LOGS_FULL_PATH}/gnb.log"; then
    break
  fi
  echo "[DEBUG] restart..."
  docker-compose -f nr-gnb.yaml restart -t 1 nr_gnb
done
popd

# wait for all jobs
for job in `jobs -p`
do
echo $job
    wait $job || echo "error: ${job}" || exit 1
done

# simple sleep for pfcp
sleep 5

pushd $CONTAINER_PROJECT_PATH
# gather logs
docker-compose -f sa-deploy.yaml logs --no-color > "${LOGS_FULL_PATH}/open5gs.log"

# cleanup
docker-compose -f nr-gnb.yaml stop -t1
docker-compose -f sa-deploy.yaml stop -t1
docker-compose -f nr-gnb.yaml rm -f
docker-compose -f sa-deploy.yaml rm -f

popd
