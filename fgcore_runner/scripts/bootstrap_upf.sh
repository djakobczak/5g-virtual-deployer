#!/bin/bash
set -ux

CONFIG_DIR=${1:-"/home/ops/nf_configs"}

open5gs-upfd -c "${CONFIG_DIR}/upf.yml" &
