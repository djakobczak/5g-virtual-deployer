#!/bin/bash
set -ue

TEST_SCRIPT="${1:-"test_bootstrap_time_vms.sh"}"
NUMBER_OF_TESTS="${2:-"20"}"
shift 2

if [[ ! -f "$TEST_SCRIPT" ]]; then
    echo "Test script (${TEST_SCRIPT}) does not exist, exit..."
    exit 1
fi


for i in $(seq 1 ${NUMBER_OF_TESTS})
do
    echo "Start test ${i}..."
    bash "${TEST_SCRIPT}" $@
    sleep 10
done
