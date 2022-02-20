from email.policy import default
import ipaddress
import logging
from pathlib import Path

import click

from fgcore_runner.modules.env import EnvManager
from fgcore_runner.modules.templar import CloudTemplar, CoreIpSchema, NfTemplar
from fgcore_runner.utils import generate_mac


TEMPLATES_DIR = Path(Path(__file__).resolve().parent.parent, 'templates')
WORKING_DIR = str(Path.home() / '5gcore-vms-wd')
NF_TEMPLATES_DIR = str(Path(TEMPLATES_DIR) / 'nf_configs')
NF_CONFIG_DIR = str(Path(WORKING_DIR) / 'nf_configs')
EXT_IP_SUBNET = ipaddress.ip_network('192.168.122.0/24')
SBI_IP_SUBNET = ipaddress.ip_network('127.0.0.0/24')

LOG = logging.getLogger(__name__)


@click.group()
@click.pass_context
@click.option("--working-dir", type=click.STRING, default=WORKING_DIR)
@click.option("--templates-dir", type=click.STRING, default=TEMPLATES_DIR)
@click.option('--ext_net', type=click.STRING, default=EXT_IP_SUBNET, show_default=True)
@click.option('--sbi_net', type=click.STRING, default=SBI_IP_SUBNET, show_default=True)
def env(ctx, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj['env'] = EnvManager(kwargs.get("working_dir"))
    ctx.obj['templar'] = CloudTemplar(kwargs.get("templates_dir"))  # !TODO add key path
    ctx.obj['ext_net'] = ipaddress.IPv4Network(kwargs.get('ext_net'))
    ctx.obj['sbi_net'] = ipaddress.IPv4Network(kwargs.get('sbi_net'))


@env.command()
@click.pass_context
@click.argument("name")
# @click.option("--host_ip_part", type=click.IntRange(min=2, max=254), required=True,
#               help="Host part (X) of network 192.168.122.X")
@click.option("--type", type=click.Choice(["cplane", "uplane", "gnodeb", "ue"]),
              default="cplane")
def add(ctx, **kwargs):
    """ Add vm to environment """
    env = ctx.obj["env"]
    templar = ctx.obj["templar"]
    name = kwargs.get("name")
    vm_type = kwargs.get('type')
    ipschema = CoreIpSchema(sbi_net= ctx.obj["sbi_net"],
                            ext_net=ctx.obj['ext_net'])

    if vm_type == 'cplane':
        ip = ipschema.ext_ip
    else:
        raise NotImplementedError(f"Type {vm_type} not supported yet")

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


@env.group()
@click.pass_context
@click.option("--nf-config-dir", default=NF_TEMPLATES_DIR, show_default=True)
def config(ctx, **kwargs):
    ctx.ensure_object(dict)
    ctx.obj['templar'] = NfTemplar(kwargs.get("nf_config_dir"))


@config.command()
@click.pass_context
def generate(ctx, **kwargs):
    templar = ctx.obj['templar']
    env = ctx.obj['env']

    ipschema = CoreIpSchema(sbi_net= ctx.obj["sbi_net"],
                            ext_net=ctx.obj['ext_net'])
    configs = templar.generate(ipschema)
    for service_name, config in configs.items():
        path = Path(env.nf_configs_dir, f'{service_name}.yml')
        templar.save(config, path)
    LOG.info(f"All configs saved at {env.nf_configs_dir}")
