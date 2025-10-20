#
# (c) 2025 Yoichi Tanibayashi
#
"""Display off command."""

import time

import click

from .. import ST7789V, __version__, click_common_opts, get_logger


@click.command(help="sleep display")
@click_common_opts(__version__)
def sleep(ctx, debug):
    """Turns the display off by entering sleep mode."""
    __log = get_logger(__name__, debug)

    cmd_name = ctx.command.name
    __log.debug("cmd_name=%s", cmd_name)

    __log.info("Putting display to sleep...")

    try:
        with ST7789V() as lcd:
            time.sleep(0.5)  # ensure lcd is ready
            # Send sleep command to the display controller
            lcd.sleep()
            time.sleep(0.1)  # Short delay to ensure command is processed

    except Exception as e:
        __log.error("%s: %s", type(e).__name__, e)
        exit(1)

    finally:
        __log.info("Done.")
