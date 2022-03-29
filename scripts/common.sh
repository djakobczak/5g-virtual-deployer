#!/bin/bash
set -u

BOOTSTRAP_GNB_SCRIPT="/home/ops/scripts/bootstrap_gnb.sh"
BOOTSTRAP_UE_SCRIPT="/home/ops/scripts/bootstrap_ue.sh"


__restart_splitted_cplane(){
    echo "Restarting cplane..."
    ssh ops@192.168.122.30 "sudo systemctl restart mongodb"
    ssh ops@192.168.122.13 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-nrfd"
    ssh ops@192.168.122.10 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-amfd"
    ssh ops@192.168.122.11 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-ausfd"
    ssh ops@192.168.122.12 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-bsfd"
    ssh ops@192.168.122.14 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-pcfd"
    ssh ops@192.168.122.16 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-smfd"
    ssh ops@192.168.122.18 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-udrd"
    ssh ops@192.168.122.19 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-udmd"
    ssh ops@192.168.122.20 "sudo rm -f /open5gs/install/var/log/open5gs/*; sudo systemctl restart open5gs-nssfd"
    ssh ops@192.168.122.10 "sudo systemctl status open5gs-amfd"
}


__start_gnb_bg(){
    local LOG_FILE=${1}
    ssh ops@192.168.122.50 "nohup sudo bash ${BOOTSTRAP_GNB_SCRIPT} &> ${LOG_FILE} &"
}


__start_ue_bg(){
    local LOG_FILE=${1}
    ssh ops@192.168.122.60 "nohup sudo bash ${BOOTSTRAP_UE_SCRIPT} 1 1 &> ${LOG_FILE} &"
}


__stop_gnb(){
    ssh ops@192.168.122.50 "sudo pkill -f $(basename ${BOOTSTRAP_GNB_SCRIPT})"
    ssh ops@192.168.122.50 "sudo pkill -f nr-gnb"
}


__stop_ue(){
    ssh ops@192.168.122.60 "sudo pkill -f $(basename ${BOOTSTRAP_UE_SCRIPT})"
    ssh ops@192.168.122.60 "sudo pkill -f nr-ue"
}


__run_on_ue_fg(){
    local cmd="${1}"
    local log_file="${2:-"/tmp/cmd-$(date +"%H-%M-%S-%6N").log"}"
    ssh ops@192.168.122.60 "$cmd &> $log_file"
}


__start_splitted_cplane(){
    virsh list --all --name | grep -v cplane | xargs -L1 -I{} virsh start {}
}