
import logging
from pathlib import Path
from pprint import pprint
from random import randint

from modules.cloud_runner import VmManager, EnvManager
from modules.templar import CloudTemplar

LOGGER_FORMAT = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
logging.basicConfig(format=LOGGER_FORMAT, datefmt='%I:%M:%S %p', level=logging.DEBUG)

WORKING_DIR = str(Path.home() / '5gcore-vms-wd')
BASE_IMG = 'focal-server-cloudimg-amd64.img'
DEBIAN_IMG = 'debian-10-generic-arm64-20211011-792.qcow2'
BASE_5GCORE_IMG = '5gcore-base.qcow2'

TEMPLATES_DIR = Path(Path(__file__).resolve().parent, 'templates')


def _generate_mac():
    r255 = lambda: randint(16, 255)
    return f'52:54:00:{r255():x}:{r255():x}:{r255():x}'


base_cplane_vm_config = {
    'name': 'builder',
    'base_img': BASE_IMG,
    'mac': _generate_mac(),
    'ip': '192.168.122.250'
}

vm01_confg = {
    'name': 'cplane01',
    'base_img': BASE_5GCORE_IMG,
    'mac': _generate_mac(),
    'ip': '192.168.122.100'
}

vm02_confg = {
    'name': 'uplane01',
    'base_img': BASE_5GCORE_IMG,
    'mac': _generate_mac(),
    'ip': '192.168.122.201'
}

vm03_confg = {
    'name': 'uplane02',
    'base_img': BASE_5GCORE_IMG,
    'mac': _generate_mac(),
    'ip': '192.168.122.202'
}


env_manger = EnvManager(WORKING_DIR)
# env_manger.clear()
# env_manger.init_vm_env(base_cplane_vm_config['name'])
# env_manger.init_vm_env(vm01_confg['name'])
# env_manger.init_vm_env(vm02_confg['name'])
env_manger.print_working_directory()

# generate cloud-init configs
templar = CloudTemplar(TEMPLATES_DIR)

# base cplane
# cloud_configs = templar.generate_cplane_node_base(**base_cplane_vm_config)
# vmpath = env_manger[base_cplane_vm_config['name']]
# templar.save(cloud_configs['user_data'], vmpath.user_data)
# templar.save(cloud_configs['network_data'], vmpath.network_data)


cr = VmManager(env_manger)
# cr.destroy_vms()

# cr.create_vm_disk(base_cplane_vm_config['name'], base_cplane_vm_config['base_img'])
# cr.create_disk_with_nocloud(base_cplane_vm_config['name'])
# cr.provision_vm(base_cplane_vm_config['name'], base_cplane_vm_config['mac'])

cloud_configs = templar.generate_cplane_node(**vm01_confg)
vmpath = env_manger[vm01_confg['name']]
templar.save(cloud_configs['user_data'], vmpath.user_data)
templar.save(cloud_configs['network_data'], vmpath.network_data)

cloud_configs = templar.generate_cplane_node(**vm02_confg)
vmpath = env_manger[vm02_confg['name']]
templar.save(cloud_configs['user_data'], vmpath.user_data)
templar.save(cloud_configs['network_data'], vmpath.network_data)
# env_manger.print_working_directory()
# pprint(cloud_configs)

# create disks based on builder image
# cr.create_vm_disk(vm01_confg['name'], base_cplane_vm_config['name'], force=True)
cr.create_vm_disk(vm02_confg['name'], base_cplane_vm_config['name'], force=True)
# cr.create_disk_with_nocloud(vm01_confg['name'])
cr.create_disk_with_nocloud(vm02_confg['name'])
# cr.provision_vm(vm01_confg['name'], vm01_confg['mac'])
cr.provision_vm(vm02_confg['name'], vm02_confg['mac'])

# cr.create_disk_image(mvm_config['name'], mvm_config['base_img'])
# cr.create_disk_with_nocloud(mvm_config['name'])
# cr.provision_vm(mvm_config['name'], mvm_config['mac'])
# cr.destroy_vms(all=True)

# cr.create_disk_image(vm01_confg['name'], vm01_confg['base_img'])
# cr.create_disk_with_nocloud(vm01_confg['name'])
# cr.provision_vm(vm01_confg['name'], vm01_confg['mac'])

# cr.create_disk_image(vm02_confg['name'], vm02_confg['base_img'])
# cr.create_disk_with_nocloud(vm02_confg['name'])
# cr.provision_vm(vm02_confg['name'], vm02_confg['mac'])


#!TODO
"""
change flow:
- create vm and build open5gcore
- snapshot vm disk
- create vms based on snapshot with builded deps
"""