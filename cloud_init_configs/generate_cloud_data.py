from pathlib import Path
from random import randint, seed

from typing import Any, Dict 

from jinja2 import Template
from yaml import dump


USER_DATA_TEMPLATE = str(Path('templates', 'user-data.yaml.j2'))
NETWORK_DATA_TEMPLATE = str(Path('templates', 'network-data.yaml.j2'))
SSH_PUB_KEY = str(Path('keys', 'hyper_id_rsa.pub'))


def generate_template(src: str, dst: str = None,
                      **jinja_vars) -> Dict[str, Any]:
    with open(src, 'r') as fd:
        template= Template(fd.read())
    generated = template.render(jinja_vars)

    if dst:
        with open(dst, 'w+') as out_fd:
            out_fd.write(generated)

    return generated


def _save_yaml(content: str, dst: str, force: bool = False) -> None:
    dst = Path(dst)
    if force:
        dst.parent.mkdir(parents=True, exist_ok=True)
    print(content)
    with open(dst, 'w+') as out_fd:
        dump(content, out_fd, default_flow_style=False)


def _generate_kvm_mac():
    r255 = lambda: randint(0, 255)
    return f'52:54:00:{r255():x}:{r255():x}:{r255():x}'


if __name__ == '__main__':
    with open(SSH_PUB_KEY, 'r') as key_fd:
        key = key_fd.read()

    jinja_vars = {
        'hostname': 'cplane01',
        'keys': [key],
        'packages': ['python3']
    }
    network_vars = {
        'interfaces': [
            {
                'name': 'eth01',
                'mac': _generate_kvm_mac(),
                'addresses': ['192.168.122.100'],
                'gateway4': '192.168.122.1',
                'dns_servers': '8.8.8.8',
            }
        ]
    }
    print(generate_template(USER_DATA_TEMPLATE, 'configs_generated/user_data_config.yaml', **jinja_vars))
    print(generate_template(NETWORK_DATA_TEMPLATE, 'configs_generated/net_config.yaml', **network_vars))
    print(generate_template(NETWORK_DATA_TEMPLATE, 'configs_generated/net_config.yaml', **network_vars))