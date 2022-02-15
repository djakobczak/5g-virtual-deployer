import logging
from pathlib import Path

import click

from fgcore_runner.modules.env import EnvManager
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
def create(ctx, **kwargs):
    envm = ctx.obj['envm']
    virtm = ctx.obj['virtm']

    vms = envm.get_vms()
    # LOG.debug(f"Found vms: {vms}")
    for vm in vms:
        if VM_TYPE_BUILDER in vm.vm_name:
            continue
        LOG.info(f"Provision vm {vm.vm_name}")
        # virtm.provision_vm(vm.vm_name)
