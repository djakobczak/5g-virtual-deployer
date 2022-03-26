#!/bin/bash
set -u

CPU_USAGE_UPF_FILENAME="/home/ops/monitoring/cpu_upf_${TEST_UNIQSUFIX}.log"
MEMORY_USAGE_UPF_FILENAME="/home/ops/monitoring/memory_upf_${TEST_UNIQSUFIX}.log"
CPU_USAGE_CPLANE_FILENAME="/home/ops/monitoring/cpu_cplane_${TEST_UNIQSUFIX}.log"
MEMORY_USAGE_CPLANE_FILENAME="/home/ops/monitoring/memory_cplane_${TEST_UNIQSUFIX}.log"
UE_LOG_FILENAME="/home/ops/logs/connect-ue-${TEST_UNIQSUFIX}.log"
CPU_USAGE_HOST_FILENAME="host_virt_${TEST_UNIQSUFIX}.csv"
GNB_LOG_FILENAME="/home/ops/gnb-${TEST_UNIQSUFIX}.log"
