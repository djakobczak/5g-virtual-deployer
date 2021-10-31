
import logging
from pathlib import Path
from pprint import pprint
from random import randint

from configs import MVM_IP
from modules.cloud_runner import CloudInitManager, EnvManager
from modules.templar import CloudTemplar

LOGGER_FORMAT = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
logging.basicConfig(format=LOGGER_FORMAT, datefmt='%I:%M:%S %p', level=logging.DEBUG)

WORKING_DIR = str(Path.home() / '5gcore-vms-kvm')
BASE_IMG = 'focal-server-cloudimg-amd64.img'
DEBIAN_IMG = 'debian-10-generic-arm64-20211011-792.qcow2'

TEMPLATES_DIR = Path(Path(__file__).resolve().parent, 'templates')


def _generate_mac():
    r255 = lambda: randint(16, 255)
    return f'52:54:00:{r255():x}:{r255():x}:{r255():x}'


mvm_config = {
    'name': 'mvm',
    'base_img': BASE_IMG,
    'mac': _generate_mac(),
    'ip': MVM_IP
}

vm01_confg = {
    'name': 'vm01',
    'base_img': BASE_IMG,
    'mac': _generate_mac(),
    'ip': '192.168.122.100'
}

vm02_confg = {
    'name': 'vm02',
    'base_img': BASE_IMG,
    'mac': _generate_mac(),
    'ip': '192.168.122.101'
}


env_manger = EnvManager(WORKING_DIR)
env_manger.clear()
env_manger.init_vm_env(mvm_config['name'])
env_manger.init_vm_env(vm01_confg['name'])
env_manger.init_vm_env(vm02_confg['name'])

# generate cloud-init configs
templar = CloudTemplar(TEMPLATES_DIR)

# mvm
cloud_configs = templar.generate_mvm_config(**mvm_config)
vmpath = env_manger[mvm_config['name']]
templar.save(cloud_configs['user_data'], vmpath.user_data)
templar.save(cloud_configs['network_data'], vmpath.network_data)

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

cr = CloudInitManager(env_manger)
cr.create_disk_image(mvm_config['name'], mvm_config['base_img'])
cr.create_disk_with_nocloud(mvm_config['name'])
cr.provision_vm(mvm_config['name'], mvm_config['mac'])

cr.create_disk_image(vm01_confg['name'], vm01_confg['base_img'])
cr.create_disk_with_nocloud(vm01_confg['name'])
cr.provision_vm(vm01_confg['name'], vm01_confg['mac'])

# cr.create_disk_image(vm02_confg['name'])
# cr.create_disk_with_nocloud(vm02_confg['name'], vm02_confg['base_img'])
# cr.provision_vm(vm02_confg['name'], vm02_confg['mac'])
