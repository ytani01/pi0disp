#
# (c) 2025 Yoichi Tanibayashi
#
import click

from . import __version__
from .commands.off import off
from .commands.test import test
from .my_logger import get_logger

log = get_logger(__name__)

@click.group()
@click.version_option(version=__version__)
def cli():
    """
    ST7789V Display Driver CLI
    """
    pass

cli.add_command(test)
cli.add_command(off)


if __name__ == "__main__":
    cli()
