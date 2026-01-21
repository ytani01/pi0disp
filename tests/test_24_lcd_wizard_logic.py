#
# (c) 2026 Yoichi Tanibayashi
#
import pytest

from pi0disp.utils.lcd_test_pattern import determine_lcd_settings


def test_determine_lcd_settings():
    # ケース1: 全て正解
    # 入力: (ソフトウェア設定bgr, ソフトウェア設定inv), (目視色, 目視背景)
    # 期待値: (正解bgr, 正解inv)

    # ソフトウェアがRGB/Inv:Offで送っていて、ユーザーも赤/黒に見えているなら、パネルはRGB/Inv:Off
    assert determine_lcd_settings(False, False, "red", "black") == (
        False,
        False,
    )

    # ソフトウェアがRGB/Inv:Offで送っていて、ユーザーが青/黒に見えているなら、パネルはBGR/Inv:Off
    assert determine_lcd_settings(False, False, "blue", "black") == (
        True,
        False,
    )

    # ソフトウェアがRGB/Inv:Offで送っていて、ユーザーがシアン/白に見えているなら、パネルはRGB/Inv:On
    assert determine_lcd_settings(False, False, "cyan", "white") == (
        False,
        True,
    )

    # ソフトウェアがRGB/Inv:Offで送っていて、ユーザーが水色(イエローの反対など)/白に見えているなら...
    # (反転とBGRが両方起きているケース)
    # BGRで送った赤は「青」になり、それが反転すると「黄色(Yellow)」になる
    assert determine_lcd_settings(False, False, "yellow", "white") == (
        True,
        True,
    )


def test_determine_lcd_settings_invalid():
    with pytest.raises(ValueError):
        determine_lcd_settings(False, False, "unknown", "black")
