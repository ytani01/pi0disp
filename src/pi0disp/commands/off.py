#
# (c) 2025 Yoichi Tanibayashi
#
"""On/Off command."""
import time
import click

from .. import ST7789V
from ..my_logger import get_logger

log = get_logger(__name__)


@click.command()
def off():
    log.info("%s", __name__)
    
    try:
        with ST7789V() as lcd:
            # lcd.off()
            time.sleep(.5)
            lcd.sleep()

    except Exception as _e:
        log.error("%s: %s", type(_e).__name__, _e)
        exit(1)

    finally:
        log.info("done")
