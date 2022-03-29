from email.policy import default
from lib2to3.pgen2.token import STRING
import logging
from pathlib import Path

import click

from fgcore_runner.modules.env import VM_BASE_TYPES, EnvManager, VMConfig
from fgcore_runner.modules.cloud_runner import VmManager


LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option("--working-dir", type=click.STRING, default=str(Path.home() / "5gcore-vms-wd"))
def setup(ctx, **kwargs):
    ctx.ensure_object(dict)
    em = EnvManager(kwargs.get("working_dir"))
    ctx.obj['envm'] = em
    ctx.obj['virtm'] = VmManager(em)


SERVICES = [
    'amf', 'ausf', 'bsf', 'nrf', 'nssf',
    'pcf', 'pcrf', 'smf', 'udm', 'udr', 'upf',
]


@setup.command()
@click.pass_context
@click.option("--vm", type=click.STRING, multiple=True,
              help="List of vms to create, if not specified create all vms found in env")
@click.option("--create-base", is_flag=True)
@click.option("--skip-copy", is_flag=True)
@click.option("--ram", type=click.STRING, default=2048)
@click.option("--cpu", type=click.STRING, default=2)
@click.option("--nf-service", type=click.Choice(SERVICES), help='Nf service to start after boot')  # should be separate command
def create(ctx, **kwargs):
    envm = ctx.obj['envm']
    virtm = ctx.obj['virtm']

    create_base = kwargs.get("create_base")
    ram = kwargs.get('ram')
    cpus = kwargs.get('cpu')
    nf_service = kwargs.get('nf_service')
    requested_vms = [envm[name] for name in kwargs.get('vm')]
    vms = requested_vms or envm.get_vms()

    # LOG.debug(f"Found vms: {vms}")
    for vm in vms:
        vm_name = vm.vm_name
        vmconfig = VMConfig(vm)
        if not create_base and \
            vmconfig.vm_type in VM_BASE_TYPES:
            LOG.info(f'VM {vm_name} has base type, skipping because `--create_base` not set')
            continue

        if virtm.is_vm_created(vm_name):
            LOG.warning(f"VM {vm_name} already created")
            continue

        mac = vmconfig.interfaces[0]['mac']
        LOG.info(f"Provision vm {vm_name}")
        virtm.provision_vm(vm_name, mac=mac, ram=ram, vcpus=cpus)  # !TODO add check if volumes and configs created, rebuild builder with cloud-init clean
        if not create_base and not kwargs.get('skip_copy'):
            virtm.wait_for_vm_active(vm_name)
            virtm.copy_configs(vm_name)
        if nf_service:
            virtm.enable_nf_service(vm_name, nf_service)


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
