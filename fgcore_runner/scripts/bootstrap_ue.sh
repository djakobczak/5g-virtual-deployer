#!/bin/bash

set -ux

UE_NUM=${1}
NUMBER_OF_UES=${2:-"1"}
CONFIG_DIR=${3:-"/home/ops/nf_configs"}
UE_CONFIG_FILE=${4:-"ue-${UE_NUM}.yml"}

nr-ue -c "${CONFIG_DIR}/${UE_CONFIG_FILE}" -n ${NUMBER_OF_UES}
