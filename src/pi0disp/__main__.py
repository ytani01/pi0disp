#
# (c) 2025 Yoichi Tanibayashi
#
import click

from . import __version__
from .commands.off import off
from .commands.sleep import sleep
from .commands.ball_anime import ball_anime
from .commands.wake import wake
from .commands.rgb import rgb
from .commands.image import image
from .utils.my_logger import get_logger

log = get_logger(__name__)

@click.group()
@click.version_option(version=__version__)
def cli():
    """
    A CLI tool for the ST7789V Display Driver.

    Provides basic commands to test and interact with the display,
    serving as a demonstration of the pi0disp library's capabilities.
    """
    pass

cli.add_command(ball_anime)
cli.add_command(sleep)
cli.add_command(wake)
cli.add_command(off)
cli.add_command(rgb)
cli.add_command(image)


if __name__ == "__main__":
    cli()
