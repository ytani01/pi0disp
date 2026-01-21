#
# (c) 2025 Yoichi Tanibayashi
#
import click

from . import __version__, click_common_opts, get_logger
from .commands.ballanime import ballanime
from .commands.bl import bl_cmd as bl
from .commands.coltest import coltest
from .commands.image import image
from .commands.lcd_check import lcd_check
from .commands.rgb import rgb


@click.group(invoke_without_command=True)
@click_common_opts(__version__)
def cli(ctx: click.Context, debug: bool) -> None:
    """A CLI tool for the ST7789V Display Driver.

    Provides basic commands to test and interact with the display,
    serving as a demonstration of the pi0disp library's capabilities.
    """
    cmd_name = ctx.info_name
    subcmd_name = ctx.invoked_subcommand
    __log = get_logger(str(cmd_name), debug)

    __log.debug("cmd_name=%a, subcmd_name=%a", cmd_name, subcmd_name)

    if subcmd_name is None:
        print(f"{ctx.get_help()}")


cli.add_command(ballanime)
cli.add_command(rgb)
cli.add_command(image)
cli.add_command(coltest)
cli.add_command(bl)
cli.add_command(lcd_check)


if __name__ == "__main__":
    cli()
