#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for 'lcd-check' command."""

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from pi0disp.commands.lcd_check import lcd_check


@pytest.fixture
def mock_st7789v():
    with patch("pi0disp.commands.lcd_check.ST7789V") as mock_class:
        mock_instance = MagicMock()
        mock_instance.size.width = 320
        mock_instance.size.height = 240
        # For context manager support
        mock_instance.__enter__.return_value = mock_instance
        mock_class.return_value = mock_instance
        yield mock_instance


def test_lcd_check_basic(cli_mock_env, mock_st7789v):
    """'lcd-check' コマンドの基本動作テスト (4パターン)."""
    runner, _, _ = cli_mock_env

    # 4パターン分、Enterキー入力をシミュレート
    result = runner.invoke(lcd_check, ["--debug"], input="\n\n\n\n")

    assert result.exit_code == 0
    # display() が4回呼ばれているはず
    assert mock_st7789v.display.call_count == 4

    # 各呼び出しでの invert/bgr 設定を確認
    # ただし、コマンド内では disp._invert = ... と直接書き換えているので、
    # 呼び出し時の引数ではなく、インスタンスの状態を確認する必要があるが、
    # 共有インスタンスなので最後の状態しか残らないかもしれない。
    # display() に渡された画像を検証する。


def test_lcd_check_wait(cli_mock_env, mock_st7789v):
    """'lcd-check' コマンドの --wait 指定時のテスト."""
    runner, _, _ = cli_mock_env

    # --wait を短く指定して自動進行させる
    result = runner.invoke(lcd_check, ["--wait", "0.01", "--debug"])

    assert result.exit_code == 0
    assert mock_st7789v.display.call_count == 4


def test_lcd_check_filter_invert(cli_mock_env, mock_st7789v):
    """'lcd-check' コマンドの --invert フィルタテスト."""
    runner, _, _ = cli_mock_env

    # invert=True のみに絞る (2パターン: bgr=False, bgr=True)
    result = runner.invoke(lcd_check, ["--invert", "--wait", "0.01"])

    assert result.exit_code == 0
    assert mock_st7789v.display.call_count == 2


def test_lcd_check_pattern_content(cli_mock_env, mock_st7789v):
    """テストパターンの画像内容を検証する."""
    runner, _, _ = cli_mock_env

    # 特定の1パターンのみ実行
    result = runner.invoke(
        lcd_check, ["--invert", "--no-bgr", "--wait", "0.01"]
    )

    assert result.exit_code == 0
    assert mock_st7789v.display.call_count == 1

    # 渡された画像を取得
    args, _ = mock_st7789v.display.call_args
    img = args[0]
    assert isinstance(img, Image.Image)
    assert img.size == (320, 240)

    # ピクセル検証 (RGB)
    # 帯の高さ bh = min(240 // 10, 32) = 24
    # Red: [0, 24)
    # Green: [24, 48)
    # Blue: [48, 72)
    bh = min(240 // 10, 32)

    # Red 帯の中央付近
    pixel = img.getpixel((10, bh // 2))
    assert isinstance(pixel, tuple)
    r, g, b = pixel[:3]
    assert r > 200 and g == 0 and b == 0

    # Green 帯の中央付近
    pixel = img.getpixel((10, bh + bh // 2))
    assert isinstance(pixel, tuple)
    r, g, b = pixel[:3]
    assert r == 0 and g > 200 and b == 0

    # Blue 帯の中央付近
    pixel = img.getpixel((10, bh * 2 + bh // 2))
    assert isinstance(pixel, tuple)
    r, g, b = pixel[:3]
    assert r == 0 and g == 0 and b > 200

    # 背景 (y=100)
    pixel = img.getpixel((10, 100))
    assert isinstance(pixel, tuple)
    r, g, b = pixel[:3]
    assert r == 0 and g == 0 and b == 0
