from random import randint

import yaml


def generate_mac():
    r255 = lambda: randint(16, 255)
    return f'52:54:00:{r255():x}:{r255():x}:{r255():x}'



def read_yaml(path: str) -> dict:
    with open(path, "r") as stream:
        return yaml.safe_load(stream)
