#
# (c) 2026 Yoichi Tanibayashi
#
"""LCD Check command."""

import os
import time

import click

from .. import __version__
from ..disp.disp_conf import DispConf
from ..disp.st7789v import ST7789V
from ..utils.click_utils import click_common_opts
from ..utils.lcd_test_pattern import (
    WIZARD_BG,
    WIZARD_COLORS,
    determine_lcd_settings,
    draw_lcd_test_pattern,
)
from ..utils.my_conf import update_toml_settings
from ..utils.mylogger import get_logger


def run_unified_wizard(disp: ST7789V, debug: bool = False) -> dict[str, int | bool]:
    """
    Unified interactive LCD setting wizard.
    Adjust rotation, invert, and BGR settings in real-time.

    Args:
        disp: ST7789V display object.
        debug: Debug flag.

    Returns:
        A dictionary containing the selected settings.
    """
    __log = get_logger(__name__, debug)
    
    cur_rot = disp.rotation
    cur_inv = disp._invert
    cur_bgr = disp._bgr
    
    print("\n--- LCD Interactive Wizard ---")
    print("実機の表示を確認しながら、以下のキーで調整してください。")
    print("背景が『漆黒』、上から『赤・緑・青』の順に見えるのが正解です。")
    print("\n  a, b, c, d : 画面の向き (0°, 90°, 180°, 270°)")
    print("  i          : 色反転 (Invert) ON/OFF")
    print("  g          : 色順序 (BGR) ON/OFF")
    print("  h, j, k, l : 表示位置の微調整 (x_offset, y_offset)")
    print("  ENTER      : この設定で保存して終了")
    print("  q          : 中断")
    print("------------------------------")
    
    cur_x_off = disp._x_offset
    cur_y_off = disp._y_offset

    while True:
        # Update display settings
        disp._invert = cur_inv
        disp._bgr = cur_bgr
        disp._x_offset = cur_x_off
        disp._y_offset = cur_y_off
        disp.init_display()
        disp.set_rotation(cur_rot)
        
        # [CRITICAL] Access private variables to ensure consistency
        width, height = disp.size.width, disp.size.height
        
        # Clear cache to prevent artifacts during rotation/setting change
        disp._last_image = None
        
        # Create test pattern
        img = draw_lcd_test_pattern(
            width, height, cur_inv, cur_bgr
        )
        
        # Display it using 'full=True' to force clear screen
        disp.display(img, full=True)
        
        status = f"Rot:{cur_rot:3} Inv:{str(cur_inv):5} BGR:{str(cur_bgr):5} Off:({cur_x_off},{cur_y_off}) ({width}x{height})"
        print(f"\rCurrent: {status} (a-d,i,g,hjkl,ENTER) ", end="", flush=True)
        
        c = click.getchar().lower()
        if c == "a":
            cur_rot = 0
        elif c == "b":
            cur_rot = 90
        elif c == "c":
            cur_rot = 180
        elif c == "d":
            cur_rot = 270
        elif c == "i":
            cur_inv = not cur_inv
        elif c == "g":
            cur_bgr = not cur_bgr
        elif c == "h": # X offset decrease
            cur_x_off -= 1
        elif c == "l": # X offset increase
            cur_x_off += 1
        elif c == "k": # Y offset decrease
            cur_y_off -= 1
        elif c == "j": # Y offset increase
            cur_y_off += 1
        elif c in ["\r", "\n"]:
            print("\n設定を確定しました。")
            break
        elif c == "q":
            print("\n中断しました。")
            raise click.Abort()

    return {
        "rotation": cur_rot, 
        "invert": cur_inv, 
        "bgr": cur_bgr,
        "x_offset": cur_x_off,
        "y_offset": cur_y_off
    }


@click.command()
@click_common_opts(__version__)
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
@click.option(
    "--wizard",
    is_flag=True,
    help="Launch interactive wizard to identify settings",
)
def lcd_check(ctx, rotation, invert, bgr, wait, wizard, debug):
    """LCD Check tool to identify correct invert and BGR settings."""
    __log = get_logger(__name__, debug)
    __log.debug(
        "rotation=%d, invert=%s, bgr=%s, wait=%f, wizard=%s",
        rotation,
        invert,
        bgr,
        wait,
        wizard,
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

        disp = ST7789V(rotation=rotation, debug=debug)
        
        if wizard:
            result = run_unified_wizard(disp, debug=debug)
            
            if click.confirm("\n設定を保存しますか？", default=True):
                save_path = "pi0disp.toml"
                if conf and conf.settings_files:
                    for p in conf.settings_files:
                        if os.path.exists(p):
                            save_path = p
                            break
                
                __log.info("Saving settings to: %s", save_path)
                update_toml_settings(result, save_path)
                print(f"設定を保存しました: {save_path}")
            
            return

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
