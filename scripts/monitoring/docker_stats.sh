set -u

OUTNAME="${1:-"docker_stats.log"}"
INTERVAL=1

update_file() {
  docker stats --no-stream --format "table {{.Name}},{{.CPUPerc}},{{.MemUsage}},{{.NetIO}},{{.BlockIO}},{{.PIDs}}" | sort -k 1 -t ',' &>> ${OUTNAME}
  echo $(date +'%T.%3N') >> ${OUTNAME}
}

while true;
do
  update_file &
  sleep ${INTERVAL}
done
