from dataclasses import dataclass, field
import logging
from pathlib import Path
import shutil
import subprocess
from typing import List

from fgcore_runner.utils import generate_mac


LOG = logging.getLogger(__name__)

VM_TYPE_BUILDER = 'builder'
VM_TYPE_CORE = 'cplane'
VM_TYPE_UPF = 'upf'


@dataclass
class VMPath:
    working_dir: Path
    vm_name: str
    base_dir: Path = field(init=False)
    config_dir: Path = field(init=False)
    user_data: Path = field(init=False)
    network_data: Path = field(init=False)
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
        self.disk_image = self.images_dir / f'{self.vm_name}.qcow2'
        self.nocloud_disk = self.images_dir / f'{self.vm_name}-nocloud.qcow2'
        self.disk_paths = [self.disk_image, self.nocloud_disk]

        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.images_dir.mkdir(parents=True, exist_ok=True)


class EnvManager:
    def __init__(self, working_dir: str) -> None:
        self.working_dir = Path(working_dir)
        self.vms_dir = Path(working_dir) / 'vms'
        self.base_images_dir = Path(working_dir) / 'base-images'

        self.vms_dir.mkdir(parents=True, exist_ok=True)
        self.base_images_dir.mkdir(parents=True, exist_ok=True)
        self.vms = self.get_vms()

    def init_vm_env(self, name: str, vm_type: str = VM_TYPE_CORE) -> None:
        vm_env = VMPath(self.vms_dir, f"{name}-{vm_type}")
        if vm_env in self.vms:
            raise Exception(f"Env for vm {name} already exists")
        self.vms.append(vm_env)

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

    def get_vms(self) -> List[VMPath]:
        return [VMPath(self.vms_dir, p.name)
                for p in self.vms_dir.iterdir()
                if p.name != 'base-images']

    def get_vm_names(self) -> List[str]:
        return [vm_path.vm_name for vm_path in self.get_vms()]

    def get_core_vm_names(self) -> List[str]:
        return [vm_path.vm_name for vm_path in self.get_vms()
                if VM_TYPE_BUILDER not in vm_path.vm_name]

    def is_vm_initialized(self, vm_name: str) -> bool:
        return vm_name in self.get_vm_names()

    def __getitem__(self, name: str):
        try:
            return next(vmpath for vmpath in self.vms if vmpath.vm_name == name)
        except StopIteration:
            raise LookupError(f'VM with name {name} not initilized by EnvManager')


class VmManager:
    def __init__(self,
                 env_manager: EnvManager
                 ) -> None:
        self.env_manager = env_manager

    def create_vm_disk(self,
                       vm_name: str,
                       src_img_or_vm: str,
                       disk_format: str = 'qcow2',
                       disk_size: str = '10G',
                       **kwargs) -> None:
        if self.env_manager.is_vm_initialized(src_img_or_vm):
            src_img_or_vm = self.env_manager[src_img_or_vm].disk_image

        vm_disk_image = self.env_manager[vm_name].disk_image
        self.create_disk_snapshot(vm_disk_image, src_img_or_vm,
                                  disk_format, disk_size, **kwargs)

    def create_disk_snapshot(self,
                        dest_img_name: str,
                        base_img_name: str,
                        disk_format: str = 'qcow2',
                        disk_size: str = '10G',
                        **kwargs) -> None:
        """ Create snapshot from existing disk (COW) """
        base_img_path = self.env_manager.base_images_dir / base_img_name
        dest_img_path = self.env_manager.base_images_dir / dest_img_name

        if not base_img_path.is_file():
            raise FileNotFoundError(f"Base image ({base_img_path}) not found")

        if dest_img_path.is_file() and not kwargs.get("force"):
            raise FileExistsError(f"Destition image already exist ({dest_img_path})")

        # create disk image with specified size based on base image (COW)
        cmd = ['sudo', 'qemu-img', 'create',
               '-f', disk_format,
               '-F', disk_format,
               '-b', str(base_img_path),
               str(dest_img_path) ,
               str(disk_size)
        ]

        LOG.debug('Run command: %s', cmd)
        subprocess.run(cmd, check=True)

    def create_disk_with_nocloud(self,
                                 vm_name: str,
                                 metadata_path: str = None,
                                 verbosity=True):
        vmpath = self.env_manager[vm_name]

        verbose = '-v' if verbosity else ''
        net_config = []
        metadata = [metadata_path] if metadata_path else []  # unused, remove or fix

        # validate cloud configs
        if vmpath.network_data.is_file():
            self.validate_cloud_config(vmpath.network_data)
            net_config = ['--network-config', vmpath.network_data]
        self.validate_cloud_config(vmpath.user_data)

        # cloud-localds [ options ] output user-data [meta-data]
        cmd = [
            'sudo', 'cloud-localds', verbose,
            *net_config,
            vmpath.nocloud_disk,
            vmpath.user_data,
            *metadata
        ]
        LOG.debug('Run command: %s', cmd)
        subprocess.run(cmd, check=True)

    def verify_if_vm_can_be_created(self, vm_name: str):
        pass

    def provision_vm(self,
                     vm_name: str,
                     mac: str = None,
                     ram: str = '2048',
                     vcpus: str = '2',
                     os_variant: str = 'ubuntu20.04',
                     virt_type: str = 'kvm',
                     os_type: str = 'linux'):
        vmpath = self.env_manager[vm_name]

        if not mac:
            mac = generate_mac()

        disks_def = []
        for dpath in vmpath.disk_paths:
            disks_def.append('--disk')
            disks_def.append(f'path={dpath},device=disk')

        # !TODO extend network definition
        cmd = [
            'sudo',
            'virt-install',
            '--connect', 'qemu:///system',
            '--virt-type', virt_type,
            '--name', vm_name,
            *disks_def,
            '--ram', ram,
            '--vcpus', vcpus,
            '--os-type', os_type,
            '--os-variant', os_variant,
            '--import',
            '--network', f'network=default,model=virtio,mac={mac}',
            '--noautoconsole'
        ]
        LOG.debug('Run command: %s', ' '.join(cmd))
        result = subprocess.run(cmd, capture_output=True)
        if result.stderr:
            LOG.error(result)

    def validate_cloud_config(self, path: str):
        subprocess.run(['cloud-init', 'devel', 'schema',
                        '--config-file', f'{path}'],
                       check=True)

    def destroy_vms(self, *vm_names: List[str], all=False) -> None:
        virsh_out = subprocess.run(
            ['virsh', 'list', '--all', '--name'],
            check=True, capture_output=True, text=True)
        running_vm = virsh_out.stdout.strip().split()
        if all:
            vm_names = running_vm

        for vm_name in vm_names:
            if vm_name not in running_vm:
                LOG.warning(f"VM {vm_name} is not running")
                continue
            subprocess.run(['virsh', 'undefine', vm_name])
            subprocess.run(['virsh', 'destroy', vm_name])
