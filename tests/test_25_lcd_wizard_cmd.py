#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for 'lcd-check --wizard' command."""

from unittest.mock import MagicMock, patch

import pytest
from pi0disp.commands.lcd_check import lcd_check

@pytest.fixture
def mock_st7789v():
    with patch("pi0disp.commands.lcd_check.ST7789V") as mock_class:
        mock_instance = MagicMock()
        mock_instance.size.width = 320
        mock_instance.size.height = 240
        mock_instance.__enter__.return_value = mock_instance
        mock_class.return_value = mock_instance
        yield mock_instance

def test_lcd_wizard_flow(cli_mock_env, mock_st7789v):
    """ウィザードの正常系フローをテストする."""
    runner, _, _ = cli_mock_env
    
    # Q1: black (seen_bg)
    # Q2: red (seen_color)
    # Confirm: y (save)
    result = runner.invoke(lcd_check, ["--wizard"], input="black\nred\ny\n")

    assert result.exit_code == 0
    assert "推定される設定: bgr=False, invert=False" in result.output
    assert "推奨設定: bgr=False, invert=False" in result.output
    
    # init_display が 基準表示(1) + 判定後表示(1) = 2回呼ばれる
    assert mock_st7789v.init_display.call_count == 2

