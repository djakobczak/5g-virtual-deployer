from email.policy import default
from importlib.metadata import metadata
import ipaddress
import logging
from pathlib import Path
from typing import List

import click

from fgcore_runner.modules.env import VM_TYPE_BUILDER, VM_TYPE_CORE, VM_TYPE_GNB, VM_TYPE_RAN_BASE, VM_TYPE_UE, VM_TYPE_UPF, EnvManager, VMConfig
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
@click.option("--type", type=click.Choice(["cplane", "upf", "gnb", "ue", "ran_base", "core_base"]),
              default="cplane")
@click.option("--upf-idx", type=click.INT, help="Used to determine upf number, starts from 0 [UPF only]")
@click.option("--tunnel", type=click.STRING, multiple=True,
              help="Tun interface definition in <dev,cidr,dnn> format e.g. ogstun,10.45.0.1/16,internet",
              default=['ogstun1,10.45.0.1/16,internet1', 'ogstun2,10.45.0.2/16,internet2'])
def add(ctx, **kwargs):
    """ Add vm to environment """
    env = ctx.obj["env"]
    templar = ctx.obj["templar"]
    name = kwargs.get("name")
    vm_type = kwargs.get('type')
    upf_idx = kwargs.get('upf_idx')
    tunnels = kwargs.get('tunnel')

    ipschema = CoreIpSchema(sbi_net= ctx.obj["sbi_net"],
                            ext_net=ctx.obj['ext_net'])

    ip = _get_ip_based_on_type(vm_type, ipschema, upf_idx)

    env.init_vm_env(name)
    tunnels_config = _parse_tunnels_opt(tunnels)
    config = {
        "name": name,
        "mac": generate_mac(),
        "ip": ip,
        "tunnels": tunnels_config
    }
    cloud_configs = _generate_cloud_config(templar, vm_type, config)

    metadata_def = {
        'vm-type': vm_type,
        'tunnels': tunnels_config,
        'upf-idx': upf_idx
    }
    vmpath = env[config['name']]
    templar.save(cloud_configs['user_data'], vmpath.user_data)
    templar.save(cloud_configs['network_data'], vmpath.network_data)
    templar.save_yaml(metadata_def, vmpath.metadata)
    LOG.info(f"VM ({name}, {vm_type}) env initialized")


def _generate_cloud_config(templar, vm_type, config):
    if vm_type == VM_TYPE_CORE:
        cloud_configs = templar.generate_cplane_node(**config)
    elif vm_type == VM_TYPE_UPF:
        cloud_configs = templar.generate_upf_node(**config)
    elif vm_type == VM_TYPE_RAN_BASE:
        cloud_configs = templar.generate_ran_base_config(**config)
    elif vm_type in [VM_TYPE_GNB, VM_TYPE_UE]:
        cloud_configs = templar.generate_common_ran_config(**config)
    return cloud_configs


def _get_ip_based_on_type(vm_type: str, ipschema: CoreIpSchema, upf_idx: int=None) -> ipaddress.IPv4Address:
    if vm_type == VM_TYPE_CORE:
        ip = ipschema.ext_ip
    elif vm_type == VM_TYPE_UPF:
        if upf_idx is None:
            raise Exception("Vm type upf requires upf-idx")
        ip = ipschema.upfs[upf_idx]
    elif vm_type == VM_TYPE_RAN_BASE:
        ip =  ipschema.ran_builder
    elif vm_type == VM_TYPE_GNB:
        ip =  ipschema.gnb_ip
    elif vm_type == VM_TYPE_UE:
        ip =  ipschema.ue_ip
    else:
        raise NotImplementedError(f"Type {vm_type} not supported yet")
    return ip

def _parse_tunnels_opt(tunnels) -> List[dict]:
    return [
        {
            'dev': tun_tuple[0],
            'ip': tun_tuple[1],
            'dnn': tun_tuple[2]
        }
        for tun_tuple in map(lambda tun_def: tun_def.split(','), tunnels)
    ]


@env.command()
@click.pass_context
@click.argument("name")
@click.option("--force", help="Force to delte base vm env")
def remove(ctx, **kwargs):
    """ Remove vm """
    env = ctx.obj['env']
    vm_name = kwargs.get("name")
    force = kwargs.get("force")
    confirmation = click.confirm(f'This command will remove vm ({vm_name}), '
                                 'do you want to continue?')
    if confirmation:
        vmpath = env[vm_name]
        vmconfig = VMConfig(vmpath)
        if vmconfig.vm_type in [VM_TYPE_RAN_BASE, VM_TYPE_BUILDER] and not force:
            LOG.warning("In order to remove base vm you have to add --force option")
            return
        env.remove_vm(vm_name)


@env.command()
@click.pass_context
@click.option("--vm", multiple=True, help="VM to remove")  # !TODO add mutally excluded
@click.option("--all", is_flag=True , help="Clear all vms")
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
    extra_vars = _get_vm_tunnels(env)
    LOG.debug(f"Found tunnels: {extra_vars}")

    configs = templar.generate(ipschema, **extra_vars)
    for service_name, config in configs.items():
        path = Path(env.nf_configs_dir, f'{service_name}.yml')
        templar.save(config, path)
    LOG.info(f"All configs saved at {env.nf_configs_dir}")


def _get_vm_tunnels(env) -> dict:
    upf_tunnels_mappings = {}
    for vmpath in env.get_vms():
        vmconfig = VMConfig(vmpath)
        if vmconfig.vm_type != VM_TYPE_UPF:
            continue

        mapping = {
            vmpath.vm_name: vmconfig.metadata['tunnels']
        }
        upf_tunnels_mappings.update(mapping)
    return upf_tunnels_mappings
