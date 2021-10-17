# generate key-pair
KEY_PATH="keys/hyper_id_rsa"
ssh-keygen -t rsa -b 4096 -f ${KEY_PATH} -C hypervisor -N "" -q