#!/bin/bash
set -ux

: ${WEBUI_IP:="192.168.122.10"}
: ${WEBUI_PORT:="3001"}

baseUrl="http://${WEBUI_IP}:${WEBUI_PORT}/api"
tokenUrl="${baseUrl}/auth/csrf"

curl -XGET -s ${tokenUrl}| jq -r '.csrfToken'
