#!/bin/bash
set -ux

TOKEN=${1}
: ${WEBUI_IP:="192.168.122.10"}
: ${WEBUI_PORT:="3001"}

baseUrl="http://${WEBUI_IP}:${WEBUI_PORT}/api"

curl -XPOST \
 -H "Content-Type: application/json" \
 -H "X-CSRF-TOKEN: ${TOKEN}" \
 -d @subscriber.json \
 "${baseUrl}/db/Subscriber"
