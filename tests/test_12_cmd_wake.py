"""Tests for 'wake' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.wake import wake
from pi0disp.disp.disp_spi import SpiPins


@patch("pi0disp.commands.wake.ST7789V")
@patch("time.sleep")
def test_wake_success(mock_sleep, mock_st7789v):
    """'wake' コマンドの正常系テスト."""
    mock_lcd = MagicMock()
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    runner = CliRunner()
    result = runner.invoke(wake, ["--rst", "25", "--dc", "24", "--bl", "23"])

    assert result.exit_code == 0
    mock_st7789v.assert_called_once_with(pin=SpiPins(rst=25, dc=24, bl=23))
    mock_lcd.wake.assert_called_once()


def test_wake_help():
    """'wake' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(wake, ["--help"])
    assert result.exit_code == 0
    assert "wake" in result.output
