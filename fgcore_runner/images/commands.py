from pathlib import Path

import click

from fgcore_runner.modules.env import EnvManager
from fgcore_runner.modules.cloud_runner import VmManager


@click.group()
@click.pass_context
@click.option("--working-dir", type=click.STRING, default=str(Path.home() / "5gcore-vms-wd"))
def images(ctx, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj['env'] = EnvManager(kwargs.get("working_dir"))


@images.command()
@click.pass_context
@click.option("--vm-name", required=True, help="Name of VM")
@click.option("--src", required=True, help="Name of base VM or base image")
def create(ctx, **kwargs):
    """ Create images for VM """
    cr = VmManager(ctx.obj['env'])

    vm_name = kwargs.get("vm_name")
    src = kwargs.get("src")

    cr.create_vm_disk(vm_name, src, force=True)
    cr.create_disk_with_nocloud(vm_name)
