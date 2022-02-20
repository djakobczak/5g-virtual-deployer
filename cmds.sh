# generate key-pair
set -x

KEY_PATH=${1-:'keys/hyper_id_rsa'}

ssh-keygen -t rsa -b 4096 -f ${KEY_PATH} -C hypervisor -N "" -q
