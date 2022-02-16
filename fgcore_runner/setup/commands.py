import logging
from pathlib import Path

import click

from fgcore_runner.modules.env import EnvManager, VMConfig
from fgcore_runner.modules.cloud_runner import (
    VmManager, VM_TYPE_CORE, VM_TYPE_UPF, VM_TYPE_BUILDER)

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option("--working-dir", type=click.STRING, default=str(Path.home() / "5gcore-vms-wd"))
def setup(ctx, **kwargs):
    ctx.ensure_object(dict)
    em = EnvManager(kwargs.get("working_dir"))
    ctx.obj['envm'] = em
    ctx.obj['virtm'] = VmManager(em)


@setup.command()
@click.pass_context
@click.option("--vm", type=click.STRING, multiple=True,
              help="List of vms to create, if not specified create all vms found in env")
def create(ctx, **kwargs):
    envm = ctx.obj['envm']
    virtm = ctx.obj['virtm']

    requested_vms = [envm[name] for name in kwargs.get('vm')]
    vms = requested_vms or envm.get_vms()
    # LOG.debug(f"Found vms: {vms}")
    for vm in vms:
        vm_name = vm.vm_name
        if VM_TYPE_BUILDER in vm_name:
            continue

        if virtm.is_vm_created(vm_name):
            LOG.warning(f"VM {vm_name} already created")
            continue

        mac = VMConfig(vm).interfaces[0]['mac']
        LOG.info(f"Provision vm {vm_name}")
        virtm.provision_vm(vm_name, mac=mac)  # !TODO add check if volumes and configs created, rebuild builder with cloud-init clean


@setup.command()
@click.pass_context
@click.option("--vm", type=click.STRING, multiple=True,
              help="List of vms to create, if not specified create all vms found in env")
def create(ctx, **kwargs):
    envm = ctx.obj['envm']
    virtm = ctx.obj['virtm']

    requested_vms = [envm[name] for name in kwargs.get('vm')]
    vms = requested_vms or envm.get_vms()
    # LOG.debug(f"Found vms: {vms}")
    for vm in vms:
        vm_name = vm.vm_name
        if VM_TYPE_BUILDER in vm_name:
            continue

        if virtm.is_vm_created(vm_name):
            LOG.warning(f"VM {vm_name} already created")
            continue

        mac = VMConfig(vm).interfaces[0]['mac']
        LOG.info(f"Provision vm {vm_name}")
        virtm.provision_vm(vm_name, mac=mac)  # !TODO add check if volumes and configs created, rebuild builder with cloud-init clean

@setup.command()
@click.pass_context
@click.option("--vm", type=click.STRING, multiple=True,
              help="List of vms to destroy, if not "
              "specified destroy all vms found in env")
def remove(ctx, **kwargs):
    envm = ctx.obj['envm']
    virtm = ctx.obj['virtm']

    requested_vms = kwargs.get('vm')
    vms = requested_vms or envm.get_vm_names()
    LOG.info(f"Destroy vms {vms}")
    virtm.destroy_vms(*vms)
