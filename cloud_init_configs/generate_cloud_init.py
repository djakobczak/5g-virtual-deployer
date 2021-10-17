from pathlib import Path

from typing import Any, Dict 

from jinja2 import Template
from yaml import dump


USER_DATA_TEMPLATE = str(Path('templates', 'user-data.yaml.j2'))
SSH_PUB_KEY = str(Path('keys', 'hyper_id_rsa.pub'))


def generate_template(src: str, dst: str = None,
                      **jinja_vars) -> Dict[str, Any]:
    with open(src, 'r') as fd:
        template= Template(fd.read())
    generated = template.render(jinja_vars)

    if dst:
        _save_yaml(generated, dst)

    return generated


def _save_yaml(content: str, dst: str, force: bool = False) -> None:
    dst = Path(dst)
    if force:
        dst.parent.mkdir(parents=True, exist_ok=True)

    with open(dst, 'w+') as out_fd:
        dump(content, out_fd, default_flow_style=False)


if __name__ == '__main__':
    with open(SSH_PUB_KEY, 'r') as key_fd:
        key = key_fd.read()

    jinja_vars = {
        'hostname': 'cplane01',
        'keys': [key],
        'packages': ['python3']
    }
    print(generate_template(USER_DATA_TEMPLATE, None, **jinja_vars))