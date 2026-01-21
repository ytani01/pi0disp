#
# (c) 2026 Yoichi Tanibayashi
#
"""LCD Check command."""

import time

import click

from .. import __version__
from ..disp.disp_conf import DispConf
from ..disp.st7789v import ST7789V
from ..utils.click_utils import click_common_opts
from ..utils.lcd_test_pattern import draw_lcd_test_pattern
from ..utils.mylogger import get_logger


@click.command()
@click.option(
    "--rotation",
    "-r",
    type=int,
    default=90,
    show_default=True,
    help="Display rotation (0, 90, 180, 270)",
)
@click.option(
    "--invert/--no-invert",
    default=None,
    help="Force invert setting (True/False)",
)
@click.option(
    "--bgr/--no-bgr",
    default=None,
    help="Force BGR setting (True/False)",
)
@click.option(
    "--wait",
    "-w",
    type=float,
    default=0,
    help="Auto-advance wait time in seconds (0 for manual)",
)
@click_common_opts(__version__)
def lcd_check(ctx, rotation, invert, bgr, wait, debug):
    """LCD Check tool to identify correct invert and BGR settings."""
    __log = get_logger(__name__, debug)
    __log.debug(
        "rotation=%d, invert=%s, bgr=%s, wait=%f", rotation, invert, bgr, wait
    )

    # Determine tests to run
    tests = []
    if invert is not None and bgr is not None:
        tests = [{"invert": invert, "bgr": bgr}]
    elif invert is not None:
        tests = [
            {"invert": invert, "bgr": False},
            {"invert": invert, "bgr": True},
        ]
    elif bgr is not None:
        tests = [{"invert": True, "bgr": bgr}, {"invert": False, "bgr": bgr}]
    else:
        tests = [
            {"invert": True, "bgr": False},
            {"invert": True, "bgr": True},
            {"invert": False, "bgr": False},
            {"invert": False, "bgr": True},
        ]

    disp = None
    try:
        # Load config to get SPI settings if needed, but we mainly want to test
        conf = DispConf(debug=debug)
        if conf.data is None:
            __log.warning("Configuration data not found. Using defaults.")
            # We can still proceed with ST7789V defaults if needed,
            # but usually it's better to have conf.
            # ST7789V will try to load default pins if not provided.

        disp = ST7789V(rotation=rotation, debug=debug)
        width, height = disp.size.width, disp.size.height
        __log.info(
            "Display size: %dx%d, rotation=%d", width, height, rotation
        )

        print("\n--- LCD Check ---")
        print("各設定を順に表示します。")
        print(
            "『背景が黒』『上から赤・緑・青』に見えるものを探してください。"
        )

        for i, t in enumerate(tests):
            idx = i + 1
            inv_val = t["invert"]
            bgr_val = t["bgr"]

            __log.info(
                "[%d/%d] inv=%s, bgr=%s", idx, len(tests), inv_val, bgr_val
            )
            print(f"[{idx}/{len(tests)}] inv={inv_val}, bgr={bgr_val}")

            # Update display settings
            disp._invert = inv_val
            disp._bgr = bgr_val
            disp.init_display()
            disp.set_rotation(rotation)

            # Create test pattern
            img = draw_lcd_test_pattern(
                width, height, inv_val, bgr_val, idx, len(tests)
            )

            # Display it
            disp.display(img)

            if i < len(tests) - 1:
                if wait > 0:
                    __log.debug("Waiting for %f seconds...", wait)
                    time.sleep(wait)
                else:
                    input("Next (Enter)...")
            else:
                if wait > 0:
                    time.sleep(wait)
                else:
                    input("Finish (Enter).")

    except KeyboardInterrupt:
        print("\nInterrupted.")
    except Exception as e:
        __log.error("%s: %s", type(e).__name__, e)
        if debug:
            import traceback

            traceback.print_exc()
    finally:
        if disp:
            __log.debug("Closing display...")
            disp.close()
        __log.debug("Done.")
