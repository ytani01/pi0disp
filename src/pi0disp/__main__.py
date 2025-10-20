#
# (c) 2025 Yoichi Tanibayashi
#
import click

from . import __version__, click_common_opts, get_logger
from .commands.ball_anime import ball_anime
from .commands.image import image
from .commands.off import off
from .commands.rgb import rgb
from .commands.sleep import sleep
from .commands.wake import wake


@click.group(
    invoke_without_command=True,
    help="""
Display driver CLI
""",
)
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


cli.add_command(ball_anime)
cli.add_command(sleep)
cli.add_command(wake)
cli.add_command(off)
cli.add_command(rgb)
cli.add_command(image)


if __name__ == "__main__":
    cli()
