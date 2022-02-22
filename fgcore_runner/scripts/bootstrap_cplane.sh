#!/bin/bash
set -ux

CONFIG_DIR=${1:-"/home/ops/nf_configs"}

systemctl start mongodb
systemctl enable mongodb

# note: nohup is not needed
open5gs-nrfd -c "${CONFIG_DIR}/nrf.yml" &
sleep 5
open5gs-smfd -c "${CONFIG_DIR}/smf.yml" &
open5gs-amfd -c "${CONFIG_DIR}/amf.yml" &
open5gs-ausfd -c "${CONFIG_DIR}/ausf.yml" &
open5gs-udmd -c "${CONFIG_DIR}/udm.yml" &
open5gs-udrd -c "${CONFIG_DIR}/udr.yml" &
open5gs-pcfd -c "${CONFIG_DIR}/pcf.yml" &
open5gs-nssfd -c "${CONFIG_DIR}/nssf.yml" &
open5gs-bsfd -c "${CONFIG_DIR}/bsf.yml" &
