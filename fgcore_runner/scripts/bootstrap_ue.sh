set -ux

UE_NUM=${1}
CONFIG_DIR=${2:-"/home/ops/nf_configs"}

nr-ue -c "${CONFIG_DIR}/ue-${UE_NUM}.yml"
