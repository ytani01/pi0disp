#
# (c) 2025 Yoichi Tanibayashi
#
"""Backlight brightness control command."""

import click
import pigpio

from .. import __version__
from ..disp.disp_conf import DispConf
from ..utils.click_utils import click_common_opts
from ..utils.mylogger import get_logger


@click.command()
@click.argument("val", type=int)
@click.option("--bl", type=int, help="BL PIN")
@click_common_opts(__version__)
def bl_cmd(ctx, val, bl, debug):
    """Sets the backlight brightness (0-255)."""
    __log = get_logger(__name__, debug)
    __log.debug("val=%d, bl=%s", val, bl)

    # Clamp value
    val = max(0, min(255, val))

    pi = None
    try:
        if not bl:
            conf = DispConf(debug=debug)
            bl = conf.data.spi.bl
            __log.debug("bl=%s", bl)

        pi = pigpio.pi()
        if pi.connected:
            pi.set_mode(bl, pigpio.OUTPUT); print("AAA")
            pi.set_PWM_dutycycle(bl, val); print("BBB")
        else:
            raise RuntimeError(
                "Could not connect to pigpio daemon. Is it running?"
            )

    except Exception as e:
        __log.error("%s: %s", type(e).__name__, e)

    finally:
        if pi:
            __log.info("close pigpio connection")
            pi.stop()
        __log.info("Done.")
