#!/bin/bash

ACTION="${1:-"start"}"

# use virt-top for cpu usage
TEST_UNIQSUFIX="$(date +%H-%M-%S-%6N)"
# !TODO add memory usage
CPU_USAGE_UPF_FILENAME="${2:-"/home/ops/monitoring/cpu_upf_${TEST_UNIQSUFIX}.log"}"
MEMORY_USAGE_UPF_FILENAME="${3:-"/home/ops/monitoring/memory_upf_${TEST_UNIQSUFIX}.log"}"
CPU_USAGE_CPLANE_FILENAME="${4:-"/home/ops/monitoring/cpu_cplane_${TEST_UNIQSUFIX}.log"}"
MEMORY_USAGE_CPLANE_FILENAME="${5:-"/home/ops/monitoring/memory_upf_${TEST_UNIQSUFIX}.log"}"
CPU_USAGE_HOST_FILENAME="${6:-"host_virt_${TEST_UNIQSUFIX}.csv"}"

if [[ "${ACTION}" == "start" ]]; then
    # start cpu monitoring on vms
    ssh ops@192.168.122.10 "mkdir -p $(dirname ${CPU_USAGE_CPLANE_FILENAME})"
    ssh ops@192.168.122.10 "nohup sudo bash scripts/log_server_cpu_usage.sh ${CPU_USAGE_CPLANE_FILENAME} &> ${CPU_USAGE_CPLANE_FILENAME} &"
    ssh ops@192.168.122.10 "nohup free -mh -s 0.5 &> ${MEMORY_USAGE_CPLANE_FILENAME} &"
    ssh ops@192.168.122.100 "mkdir -p $(dirname ${CPU_USAGE_UPF_FILENAME})"
    ssh ops@192.168.122.100 "nohup sudo bash scripts/log_server_cpu_usage.sh ${CPU_USAGE_UPF_FILENAME} &> ${CPU_USAGE_UPF_FILENAME} &"
    ssh ops@192.168.122.100 "nohup free -mh -s 0.5 &> ${MEMORY_USAGE_UPF_FILENAME} &"
    # start host monitoring
    virt-top -d 1 --csv ${CPU_USAGE_HOST_FILENAME} --script &
elif [[ "${ACTION}" == "stop" ]]; then
    ssh ops@192.168.122.10 "sudo pkill -f "log_server_cpu_usage.sh""
    ssh ops@192.168.122.10 "sudo pkill -f "free""
    ssh ops@192.168.122.100 "sudo pkill -f "log_server_cpu_usage.sh""
    ssh ops@192.168.122.100 "sudo pkill -f "free""
    pkill -f "virt-top"
else
  echo "[ERROR] Unkown value for argument: ${ACTION}"
  exit 1
fi
