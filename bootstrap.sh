#!/bin/bash

python3 fgcore_runner/cli.py env add cplane01
python3 fgcore_runner/cli.py env add upf01 --type upf --upf-idx 1

python3 fgcore_runner/cli.py images create --vm-name cplane01 --src builder
python3 fgcore_runner/cli.py images create --vm-name upf01 --src builder

python3 fgcore_runner/cli.py env config generate

python3 fgcore_runner/cli.py setup create
