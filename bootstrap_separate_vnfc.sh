#!/bin/bash

python3 fgcore_runner/cli.py env add --ip 192.168.122.10 cp-amf
python3 fgcore_runner/cli.py env add --ip 192.168.122.11 cp-ausf
python3 fgcore_runner/cli.py env add --ip 192.168.122.12 cp-bsf
python3 fgcore_runner/cli.py env add --ip 192.168.122.13 cp-nrf
python3 fgcore_runner/cli.py env add --ip 192.168.122.14 cp-pcf
python3 fgcore_runner/cli.py env add --ip 192.168.122.16 cp-smf
python3 fgcore_runner/cli.py env add --ip 192.168.122.18 cp-udr
python3 fgcore_runner/cli.py env add --ip 192.168.122.19 cp-udm
python3 fgcore_runner/cli.py env add --ip 192.168.122.20 cp-nssf
python3 fgcore_runner/cli.py env add --ip 192.168.122.30 cp-db

python3 fgcore_runner/cli.py images create --vm-name cp-amf --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-ausf --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-bsf --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-nrf --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-pcf --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-smf --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-udr --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-udm --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-nssf --src builder
python3 fgcore_runner/cli.py images create --vm-name cp-db --src builder

python3 fgcore_runner/cli.py env --sbi-net 192.168.122.0/24 config generate --vms upf01-min-rdy

python3 fgcore_runner/cli.py setup create --vm cp-nrf --nf-service nrf
python3 fgcore_runner/cli.py setup create --vm cp-amf --nf-service amf
python3 fgcore_runner/cli.py setup create --vm cp-smf --nf-service smf
python3 fgcore_runner/cli.py setup create --vm cp-udm --nf-service udm
python3 fgcore_runner/cli.py setup create --vm cp-udr --nf-service udr
python3 fgcore_runner/cli.py setup create --vm cp-pcf --nf-service pcf
python3 fgcore_runner/cli.py setup create --vm cp-ausf --nf-service ausf
python3 fgcore_runner/cli.py setup create --vm cp-bsf --nf-service bsf
python3 fgcore_runner/cli.py setup create --vm cp-nssf --nf-service nssf
python3 fgcore_runner/cli.py setup create --vm cp-db

python3 fgcore_runner/cli.py setup remove --vm cp-amf --vm cp-smf --vm cp-nrf --vm cp-udm --vm cp-udr --vm cp-pcf --vm cp-pcf --vm cp-ausf