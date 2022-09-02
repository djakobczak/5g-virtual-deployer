# 5G Virtual Deployer

Goal of this project was to create simple tool that facilitate management of Open5GS deployment in VMs.

Main features are:
- automated building of layered VM images that can be used with QEMU
- generating configs for NFs and prepare systemd units to run NFs on VMs
- provide network configuration for VMs
- create/undefine/start/stop particular NFs
- provide set of test scripts for testing Open5GS deployment in VMs and in containers with the use of [docker_open5gs](https://github.com/herlesupreeth/docker_open5gs) project

Scripts for generating plots from test samples are available [here](https://github.com/djakobczak/plots-core).
