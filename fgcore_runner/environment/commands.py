import ipaddress
import logging
from pathlib import Path

import click

from fgcore_runner.modules.env import EnvManager
from fgcore_runner.modules.templar import CloudTemplar
from fgcore_runner.utils import generate_mac


TEMPLATES_DIR = Path(Path(__file__).resolve().parent.parent, 'templates')
WORKING_DIR = str(Path.home() / '5gcore-vms-wd')
IP_SUBNET = ipaddress.ip_network('192.168.122.0/24')

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option("--working-dir", type=click.STRING, default=WORKING_DIR)
@click.option("--templates-dir", type=click.STRING, default=TEMPLATES_DIR)
def env(ctx, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj['env'] = EnvManager(kwargs.get("working_dir"))
    ctx.obj['templar'] = CloudTemplar(kwargs.get("templates_dir"))  # !TODO add key path


@env.command()
@click.pass_context
@click.argument("name")
@click.option("--host_ip_part", type=click.IntRange(min=2, max=254), required=True,
              help="Host part (X) of network 192.168.122.X")
@click.option("--type", type=click.Choice(["cplane", "uplane"]),
              default="cplane")
def add_vm(ctx, **kwargs):
    """ Add vm to environment """
    env = ctx.obj["env"]
    templar = ctx.obj["templar"]
    name = kwargs.get("name")
    ip = IP_SUBNET[kwargs.get('host_ip_part')]

    env.add_vm(name)
    config = {
        "name": name,
        "mac": generate_mac(),  # !TODO !!! save MAC and set it in provision_vm (save config in dir structure)
        "ip": ip,
    }
    cloud_configs = templar.generate_cplane_node(**config)
    vmpath = env[config['name']]
    templar.save(cloud_configs['user_data'], vmpath.user_data)
    templar.save(cloud_configs['network_data'], vmpath.network_data)
    LOG.info("VM env initialized")


@env.command()
@click.pass_context
@click.argument("name")
def remove(ctx, **kwargs):
    """ Remove vm """
    env = ctx.obj['env']
    vms = kwargs.get("vm")
    vm_name = kwargs.get("name")
    confirmation = click.confirm(f'This command will remove vm ({vm_name}), '
                                 'do you want to continue?')
    if confirmation:
        env.remove_vm(vm_name)


@env.command()
@click.pass_context
@click.option("--vm", multiple=True, help="VM to remove")  # !TODO add mutally excluded
@click.option("--all", is_flag=True , help="Clea all vms")
def clear(ctx, **kwargs):
    """ Clear env """
    env = ctx.obj['env']
    vms = kwargs.get("vm")
    remove_all = kwargs.get("all")
    confirmation = click.confirm('This command will remove all vms, '
                                 'do you want to continue?')
    if confirmation:
        env.clear(vms, remove_all)


@env.command()
@click.pass_context
def show(ctx, **kwargs):
    """ Show env """
    env = ctx.obj['env']
    env.print_working_directory()
