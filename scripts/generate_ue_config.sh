#!/bin/bash

UE_NUM="${1:-"1"}"
TEMPLATE_PATH="${2:-"/home/ops/nf_configs/ue-template.yml"}"
UE_CONFIG="${3:-"configs/ue-config-${UE_NUM}.yml"}"

IMSI="imsi-00101$(printf %010d ${UE_NUM})"  # pad to 10 0s
UE_CONFIG="configs/ue-config-${UE_NUM}.yml"
sed "s/|IMSI|/${IMSI}/" ${TEMPLATE_PATH} > ${UE_CONFIG}
