set -ux

CONFIG_DIR=${1:-"/home/ops/nf_configs"}

nr-gnb -c "${CONFIG_DIR}/gnb.yml"
