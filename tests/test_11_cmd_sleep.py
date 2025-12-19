"""Tests for 'sleep' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.sleep import sleep
from pi0disp.disp.disp_spi import SpiPins


@patch("pi0disp.commands.sleep.ST7789V")
@patch("time.sleep")
def test_sleep_success(mock_sleep, mock_st7789v):
    """'sleep' コマンドの正常系テスト."""
    mock_lcd = MagicMock()
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    runner = CliRunner()
    result = runner.invoke(sleep, ["--rst", "25", "--dc", "24", "--bl", "23"])

    assert result.exit_code == 0
    mock_st7789v.assert_called_once_with(pin=SpiPins(rst=25, dc=24, bl=23))
    mock_lcd.sleep.assert_called_once()


def test_sleep_help():
    """'sleep' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(sleep, ["--help"])
    assert result.exit_code == 0
    assert "sleep display" in result.output
