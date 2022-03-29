import logging
import click

from fgcore_runner.environment  import commands as env_group
from fgcore_runner.images  import commands as images_group
from fgcore_runner.setup  import commands as setup_group


LOGGER_FORMAT = '%(name)s - %(levelname)s - %(asctime)s - %(message)s'
logging.basicConfig(format=LOGGER_FORMAT, datefmt='%I:%M:%S %p', level=logging.DEBUG)


@click.group()
def fgc():
    pass


fgc.add_command(env_group.env)
fgc.add_command(images_group.images)
fgc.add_command(setup_group.setup)


def main():
    fgc()


if __name__ == "__main__":
    main()
