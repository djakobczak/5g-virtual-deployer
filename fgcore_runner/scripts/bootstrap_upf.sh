#!/bin/bash
set -ux

UE_NUM=${1}
CONFIG_DIR=${2:-"/home/ops/nf_configs"}

open5gs-upfd -c "${CONFIG_DIR}/upf-${UE_NUM}.yml" &
