#
# (c) 2025 Yoichi Tanibayashi
#
"""Display off command."""
import time
import click

from ..disp.st7789v import ST7789V
from ..utils.my_logger import get_logger

log = get_logger(__name__)


@click.command()
def sleep():
    """Turns the display off by entering sleep mode."""
    log.info("Putting display to sleep...")

    try:
        with ST7789V() as lcd:
            time.sleep(.5)  # ensure lcd is ready
            # Send sleep command to the display controller
            lcd.sleep()
            time.sleep(0.1)  # Short delay to ensure command is processed

    except Exception as e:
        log.error("%s: %s", type(e).__name__, e)
        exit(1)

    finally:
        log.info("Done.")
