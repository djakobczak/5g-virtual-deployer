#!/bin/bash
set -ux

USERNAME=${1}
IP=${2}
SRC_DIR=${3}
DST_DIR=${4}
shift 4
SERVICES=($@)

echo "Copy config services ${SERVICES[@]} from ${SRC_DIR} to ${IP}:${DST_DIR}"

for serviceName in "${SERVICES[@]}"; do
    serviceFile="${serviceName}.yml"
    serviceFilePath="${SRC_DIR}/${serviceFile}"
    if [ ! -f ${serviceFilePath} ]; then
      echo "File ${serviceFilePath} does not exist"
      exit 1
    fi

    echo "scp ${serviceFilePath} ${USERNAME}@${IP}:${DST_DIR}"
done
