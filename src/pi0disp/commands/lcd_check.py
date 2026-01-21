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
from ..utils.lcd_test_pattern import (
    WIZARD_BG,
    WIZARD_COLORS,
    determine_lcd_settings,
    draw_lcd_test_pattern,
)
from ..utils.mylogger import get_logger


def run_wizard(disp, rotation, debug=False):
    """Interactive wizard flow."""
    __log = get_logger(__name__, debug)
    
    print("\n--- LCD Settings Wizard ---")
    print("実機のLCD表示を確認しながら、以下の質問に答えてください。")
    
    # 基準設定で表示 (RGB, Invert Off)
    current_inv = False
    current_bgr = False
    disp._invert = current_inv
    disp._bgr = current_bgr
    disp.init_display()
    disp.set_rotation(rotation)
    
    width, height = disp.size.width, disp.size.height
    img = draw_lcd_test_pattern(width, height, current_inv, current_bgr)
    disp.display(img)
    
    # Q1: 背景色
    print("\n[Q1] 背景の色（文字がない部分）は何色に見えますか？")
    for k, v in WIZARD_BG.items():
        print(f"  {k}: {v}")
    seen_bg = click.prompt("選択してください", type=click.Choice(WIZARD_BG.keys()), default="black")
    
    # Q2: 一番上の帯の色
    print("\n[Q2] 画面の一番上の帯（本来は赤であるべき部分）は何色に見えますか？")
    for k, v in WIZARD_COLORS.items():
        print(f"  {k}: {v}")
    seen_color = click.prompt("選択してください", type=click.Choice(WIZARD_COLORS.keys()), default="red")
    
    if seen_color == "other":
        print("\n判定できませんでした。接続や型番を再確認してください。")
        return None

    try:
        res_bgr, res_inv = determine_lcd_settings(current_bgr, current_inv, seen_color, seen_bg)
        
        print("\n--- 判定結果 ---")
        print(f" 推定される設定: bgr={res_bgr}, invert={res_inv}")
        print("\nこの設定で再表示します...")
        
        disp._invert = res_inv
        disp._bgr = res_bgr
        disp.init_display()
        disp.set_rotation(rotation)
        img = draw_lcd_test_pattern(width, height, res_inv, res_bgr)
        disp.display(img)
        
        print("正しく表示されましたか？（背景が黒、上から赤・緑・青）")
        if click.confirm("正解の場合、設定を保存しますか？", default=True):
            return {"bgr": res_bgr, "invert": res_inv}
            
    except ValueError as e:
        print(f"\nエラー: {e}")
        
    return None


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
            result = run_wizard(disp, rotation, debug=debug)
            if result:
                print(f"\n推奨設定: bgr={result['bgr']}, invert={result['invert']}")
                print("TODO: Phase 3 で設定ファイルの自動保存を実装します。")
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
