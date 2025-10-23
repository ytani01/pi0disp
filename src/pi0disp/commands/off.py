#
# (c) 2025 Yoichi Tanibayashi
#
"""Display off command."""

import time

import click

from .. import ST7789V, __version__, click_common_opts, get_logger


@click.command(help="off")
@click.option(
    "--rst", type=int, default=25, show_default=True, help="RST PIN"
)
@click.option(
    "--dc", type=int, default=24, show_default=True, help="DC PIN"
)
@click.option(
    "--bl", type=int, default=23, show_default=True, help="BL PIN"
)
@click_common_opts(__version__)
def off(ctx, rst, dc, bl, debug) -> None:
    """Turns the display off."""
    __log = get_logger(__name__, debug)
    __log.debug("rst=%s, dc=%s, bl=%s", rst, dc, bl)

    cmd_name = ctx.command.name
    __log.debug("cmd_name=%s", cmd_name)

    __log.info("OFF...")
    try:
        with ST7789V(rst_pin=rst, dc_pin=dc, backlight_pin=bl) as lcd:
            time.sleep(0.5)  # ensure lcd is ready
            # Send sleep command to the display controller
            lcd.dispoff()
            time.sleep(0.1)  # Short delay to ensure command is processed

    except Exception as e:
        __log.error("%s: %s", type(e).__name__, e)
        exit(1)

    finally:
        __log.info("Done.")
