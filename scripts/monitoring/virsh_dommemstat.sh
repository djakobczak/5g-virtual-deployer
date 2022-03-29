#!/bin/bash
set -u

OUTNAME="${1:-"virsh_dommemstat.log"}"
INTERVAL=1

update_file() {
  virsh list --name | xargs -L1 -I{} sh -c "printf {},; virsh dommemstat {} | grep rss | sed 's/rss//'" &>> ${OUTNAME}
  echo "timestamp,$(date +'%T.%3N')" >> ${OUTNAME}
}

while true;
do
  update_file &
  sleep ${INTERVAL}
done
