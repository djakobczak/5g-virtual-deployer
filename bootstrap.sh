#!/bin/bash

python3 fgcore_runner/cli.py env add cplane01
python3 fgcore_runner/cli.py env add upf01 --type upf --upf-idx 0
python3 fgcore_runner/cli.py env add gnb01 --type gnb
python3 fgcore_runner/cli.py env add ue --type ue

python3 fgcore_runner/cli.py images create --vm-name cplane01 --src cplane-base
python3 fgcore_runner/cli.py images create --vm-name upf01 --src builder
python3 fgcore_runner/cli.py images create --vm-name gnb01 --src ran-base
python3 fgcore_runner/cli.py images create --vm-name ue --src ran-base

python3 fgcore_runner/cli.py env config generate

python3 fgcore_runner/cli.py setup create

# clear
# python3 fgcore_runner/cli.py setup remove
# python3 fgcore_runner/cli.py env clear