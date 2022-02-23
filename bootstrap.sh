#!/bin/bash

python3 fgcore_runner/cli.py env add cplane01
python3 fgcore_runner/cli.py env add upf01 --type upf --upf-idx 1
python3 fgcore_runner/cli.py env add gnb01 --type gnb
python3 fgcore_runner/cli.py env add ue --type ue

python3 fgcore_runner/cli.py images create --vm-name cplane01 --src builder
python3 fgcore_runner/cli.py images create --vm-name upf01 --src builder
python3 fgcore_runner/cli.py images create --vm-name gnb --src ran-base
python3 fgcore_runner/cli.py images create --vm-name ue --src ran-base

python3 fgcore_runner/cli.py env config generate

python3 fgcore_runner/cli.py setup create
