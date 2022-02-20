set -ux

USERNAME=${1-"ops"}
IP=${2-"192.168.122.10"}
SRC_DIR=${3-"/home/dawid/5gcore-vms-wd/nf_configs"}
DST_DIR=${4-"/home/ops/5gconfigs"}

services=('amf' 'ausf' 'bsf' 'nrf' 'nssf' 'pcf' 'smf' 'udm' 'udr')
bash copy2vm.sh ${USERNAME} ${IP} ${SRC_DIR} ${DST_DIR} ${services[@]}
