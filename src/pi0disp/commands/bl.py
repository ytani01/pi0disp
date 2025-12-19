#
# (c) 2025 Yoichi Tanibayashi
#
"""Backlight brightness control command."""

import click

from .. import ST7789V, __version__, click_common_opts, get_logger
from ..disp.disp_spi import SpiPins


@click.command(help="set backlight brightness")
@click.argument("val", type=int)
@click.option(
    "--rst", type=int, default=25, show_default=True, help="RST PIN"
)
@click.option("--dc", type=int, default=24, show_default=True, help="DC PIN")
@click.option("--bl", type=int, default=23, show_default=True, help="BL PIN")
@click_common_opts(__version__)
def bl_cmd(ctx, val, rst, dc, bl, debug):
    """Sets the backlight brightness (0-255)."""
    __log = get_logger(__name__, debug)
    __log.debug("val=%d, rst=%s, dc=%s, bl=%s", val, rst, dc, bl)

    # Clamp value
    val = max(0, min(255, val))

    try:
        # Use with statement to ensure proper initialization and cleanup.
        # Note: ST7789V will initialize at full brightness, then we set it.
        # If we wanted to avoid the flash, we'd need to modify the constructor.
        with ST7789V(pin=SpiPins(rst=rst, dc=dc, bl=bl)) as lcd:
            lcd.set_brightness(val)
            __log.info("Backlight brightness set to %d", val)

    except Exception as e:
        __log.error("%s: %s", type(e).__name__, e)
        exit(1)

    finally:
        __log.info("Done.")
