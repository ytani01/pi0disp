#
# (c) 2025 Yoichi Tanibayashi
#
import click

from . import __version__
from .my_logger import get_logger
from .commands.test import test

log = get_logger(__name__)

@click.group()
@click.version_option(version=__version__)
def cli():
    """
    ST7789V Display Driver CLI
    """
    pass

cli.add_command(test)



if __name__ == "__main__":
    cli()
