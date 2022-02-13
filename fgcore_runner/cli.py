import logging
import click

from fgcore_runner.env  import commands as env_group


LOGGER_FORMAT = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
logging.basicConfig(format=LOGGER_FORMAT, datefmt='%I:%M:%S %p', level=logging.DEBUG)


@click.group()
def fgc():
    pass


fgc.add_command(env_group.env)


if __name__ == "__main__":
    fgc()
