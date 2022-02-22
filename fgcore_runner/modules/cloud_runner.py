from dataclasses import dataclass, field
import logging
from pathlib import Path
import subprocess
from typing import List
from time import sleep

from fgcore_runner.modules.env import VM_TYPE_CORE, VM_TYPE_UPF, EnvManager, VMConfig
from fgcore_runner.utils import generate_mac


LOG = logging.getLogger(__name__)

SCRIPT_DIR = Path(Path(__file__).resolve().parent.parent, 'scripts')
OPERATOR_USERNAME = "ops"
VM_HOME_DIR = Path("/", "home", OPERATOR_USERNAME)
NF_CONFIGS_LOCAL = Path.home() / '5gcore-vms-wd' / 'nf_configs'
COPY_SCRIPTS = [
    {'src': str(NF_CONFIGS_LOCAL), 'dst': str(VM_HOME_DIR / 'nf_configs')},
    {'src': str(SCRIPT_DIR), 'dst': str(VM_HOME_DIR)},
]


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
        created_vm = self.get_vms_created()
        running_vms = self.get_vms_running()
        if all:
            vm_names = created_vm

        for vm_name in vm_names:
            if vm_name not in created_vm:
                LOG.warning(f"VM {vm_name} is not created")
                continue
            subprocess.run(['virsh', 'undefine', vm_name])

            if vm_name not in running_vms:
                LOG.warning(f"VM {vm_name} is not running")
                continue
            subprocess.run(['virsh', 'destroy', vm_name])

    def get_vms_created(self) -> List[str]:
        virsh_out = subprocess.run(
            ['virsh', 'list', '--all', '--name'],
            check=True, capture_output=True, text=True)
        created_vms = virsh_out.stdout.strip().split()
        return created_vms

    def get_vms_running(self) -> List[str]:
        virsh_out = subprocess.run(
            ['virsh', 'list', '--name'],
            check=True, capture_output=True, text=True)
        running_vms = virsh_out.stdout.strip().split()
        return running_vms

    def is_vm_created(self, name: str) -> bool:
        return name in self.get_vms_created()

    def copy_configs(self, vm_name: str) -> None:
        for copy_def in COPY_SCRIPTS:
            src = copy_def.get('src')
            dst = copy_def.get('dst')
            self.scp_to_vm(vm_name, src, dst)

    def wait_for_vm_active(self, vm_name: str):
        vmpath = self.env_manager[vm_name]
        vm_config = VMConfig(vmpath)
        vm_ip = vm_config.ips[0]  # !TODO add waiter
        cmd = [
            'ping', '-c',
        ]
        LOG.debug("Sleep for 15s...")
        sleep(15)

    def scp_to_vm(self, vm_name: str, src: str, dst: str, login: str = 'ops'):
        vmpath = self.env_manager[vm_name]
        vm_config = VMConfig(vmpath)
        vm_ip = vm_config.ips[0]
        target = f"{login}@{vm_ip}:{dst}"
        cmd = ["scp", "-r", src, target]
        LOG.debug("Run command: '{}'".format(' '.join(cmd)))
        subprocess.run(cmd, check=True)
