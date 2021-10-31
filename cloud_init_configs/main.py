
import logging
from pathlib import Path
from pprint import pprint
from random import randint

from modules.cloud_runner import CloudInitManager, EnvManager
from modules.templar import CloudTemplar

LOGGER_FORMAT = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
logging.basicConfig(format=LOGGER_FORMAT, datefmt='%I:%M:%S %p', level=logging.DEBUG)

WORKING_DIR = str(Path.home() / '5gcore-vms-kvm')
BASE_IMG = 'focal-server-cloudimg-amd64.img'

TEMPLATES_DIR = Path(Path(__file__).resolve().parent, 'templates')

vm01_confg = {
    'name': 'vm01',
    'base_img': BASE_IMG
}
r255 = lambda: randint(0, 255)
mac = f'52:54:00:{r255():x}:{r255():x}:{r255():x}'

env_manger = EnvManager(WORKING_DIR)
env_manger.init_vm_env(vm01_confg['name'])

# generate cloud-init configs
templar = CloudTemplar(TEMPLATES_DIR)
cloud_configs = templar.generate_cplane_node(vm01_confg['name'], mac)
vmpath = env_manger[vm01_confg['name']]
templar.save(cloud_configs['user_data'], vmpath.user_data)
templar.save(cloud_configs['network_data'], vmpath.network_data)
env_manger.print_working_directory()
# pprint(cloud_configs)

cr = CloudInitManager(env_manger, BASE_IMG)
cr.create_disk_image(vm01_confg['name'])
cr.create_disk_with_nocloud(vm01_confg['name'])
cr.provision_vm(vm01_confg['name'], mac)
