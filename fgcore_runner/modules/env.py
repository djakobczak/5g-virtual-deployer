from dataclasses import dataclass, field
import logging
from pathlib import Path
import shutil
import subprocess
from typing import List

from fgcore_runner.utils import read_yaml


LOG = logging.getLogger(__name__)

VM_TYPE_BUILDER = 'builder'
VM_TYPE_CORE = 'cplane'
VM_TYPE_UPF = 'upf'
VM_TYPE_RAN_BASE = 'ran_base'
VM_TYPE_GNB = 'gnb'
VM_TYPE_UE = 'ue'
VM_TYPE_TEST = 'test'
VM_BASE_TYPES = [VM_TYPE_BUILDER, VM_TYPE_RAN_BASE, VM_TYPE_TEST]
VM_TYPES =[
    VM_TYPE_BUILDER,
    VM_TYPE_RAN_BASE,
    VM_TYPE_CORE,
    VM_TYPE_UPF,
    VM_TYPE_GNB,
    VM_TYPE_UE,
    VM_TYPE_TEST
]

@dataclass
class VMPath:
    working_dir: Path
    vm_name: str
    base_dir: Path = field(init=False)
    config_dir: Path = field(init=False)
    user_data: Path = field(init=False)
    network_data: Path = field(init=False)
    metadata: Path = field(init=False)
    images_dir: Path = field(init=False)
    disk_image: Path = field(init=False)
    nocloud_disk: Path = field(init=False)
    disk_paths: List[Path] = field(init=False)

    def __post_init__(self):
        self.base_dir = self.working_dir / self.vm_name
        self.config_dir = self.base_dir / 'configs'
        self.images_dir = self.base_dir / 'images'
        self.user_data = self.config_dir / 'user-data.yaml'
        self.network_data = self.config_dir / 'network-data.yaml'
        self.metadata = self.config_dir / 'metadata.yaml'
        self.disk_image = self.images_dir / f'{self.vm_name}.qcow2'
        self.nocloud_disk = self.images_dir / f'{self.vm_name}-nocloud.qcow2'
        self.disk_paths = [self.disk_image, self.nocloud_disk]

    def init_paths(self):
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)

    def __str__(self) -> str:
        return self.vm_name

    def __repr__(self) -> str:
        return self.vm_name


class VMConfig:
    def __init__(self, vmpath: VMPath) -> None:
        self.vmpath = vmpath

    @property
    def network_data(self) -> dict:
        return read_yaml(self.vmpath.network_data)

    @property
    def user_data(self) -> dict:
        return read_yaml(self.vmpath.user_data)

    @property
    def metadata(self) -> dict:
        return read_yaml(self.vmpath.metadata)

    @metadata.setter
    def metadata(self, update_dict: dict) -> None:
        metadata_dict = self.metadata
        metadata_dict.update(update_dict)

    @property
    def interfaces(self) -> List[dict]:
        net_config = self.network_data['ethernets']
        ifaces = [
            {
                'mac': iface_def['match']['macaddress'],
                'ips': iface_def['addresses'],
                'gw': iface_def['gateway4'],
                'name': eth_name
            }
            for eth_name, iface_def in net_config.items()
        ]
        return ifaces

    @property
    def ips(self) -> List[str]:
        return [ip.split('/')[0]
                for iface in self.interfaces
                for ip in iface['ips']]

    @property
    def vm_type(self) -> str:
        return self.metadata.get('vm-type')


class EnvManager:
    def __init__(self, working_dir: str) -> None:
        self.working_dir = Path(working_dir)
        self.vms_dir = Path(working_dir) / 'vms'
        self.base_images_dir = Path(working_dir) / 'base-images'
        self.nf_configs_dir = Path(working_dir) / 'nf_configs'

        self.vms_dir.mkdir(parents=True, exist_ok=True)
        self.base_images_dir.mkdir(parents=True, exist_ok=True)
        self.nf_configs_dir.mkdir(parents=True, exist_ok=True)
        self.vms = self.get_vms(exclude_builder=False)

    def init_vm_env(self, name: str) -> None:
        vm_env = VMPath(self.vms_dir, name)
        if vm_env in self.vms:
            raise Exception(f"Env for vm {name} already exists")
        vm_env.init_paths()
        self.vms.append(vm_env)

    def remove_vm(self, name: str) -> None:
        vm_path = VMPath(self.vms_dir, name)
        LOG.debug(f"VMs: {self.vms}")
        if vm_path not in self.vms:
            raise Exception(f"Env for vm {name} does not exists")
        LOG.info(f'Remove {vm_path.base_dir}')
        shutil.rmtree(vm_path.base_dir)
        self.vms.remove(vm_path)

    def clear(self, vm_names=None):
        LOG.info('Clear all vms')
        for path in self.get_vms():
            if not vm_names or path.vm_name in vm_names:
                LOG.debug(f'Remove {path.base_dir}')
                shutil.rmtree(path.base_dir)
                self.vms.remove(path)

    def print_working_directory(self) -> None:
        # requires tree installed
        subprocess.run(['tree', self.working_dir], check=True)

    def get_vms(self, exclude_builder: bool = True) -> List[VMPath]:
        vms = [VMPath(self.vms_dir, p.name)
                for p in self.vms_dir.iterdir()
                if p.name != 'base-images']
        if exclude_builder:
            vms = list(filter(
                lambda vm: VMConfig(vm).vm_type not in VM_BASE_TYPES, vms))
        print(vms)
        return vms

    def get_vm_names(self, exclude_builder: bool = True) -> List[str]:
        vm_names = [vm_path.vm_name for vm_path in self.get_vms(exclude_builder=exclude_builder)]
        return vm_names

    def get_core_vm_names(self) -> List[str]:
        return [vm_path.vm_name for vm_path in self.get_vms(exclude_builder=False)
                if VM_TYPE_BUILDER not in vm_path.vm_name]

    def is_vm_initialized(self, vm_name: str) -> bool:
        res = vm_name in self.get_vm_names(exclude_builder=False)
        LOG.debug(f"Vm {vm_name} initialized: {res}")
        return res

    def __getitem__(self, name: str):
        try:
            return next(vmpath for vmpath in self.vms if vmpath.vm_name == name)
        except StopIteration:
            raise LookupError(f'VM with name {name} not initilized by EnvManager')
