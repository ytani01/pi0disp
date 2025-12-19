"""Tests for 'off' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.off import off
from pi0disp.disp.disp_spi import SpiPins


@patch("pi0disp.commands.off.ST7789V")
def test_off_success(mock_st7789v):
    """'off' コマンドの正常系テスト."""
    # ST7789V インスタンスのモック
    mock_lcd = MagicMock()
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    runner = CliRunner()
    result = runner.invoke(off, ["--rst", "25", "--dc", "24", "--bl", "23"])

    assert result.exit_code == 0
    # ST7789V が正しい引数で初期化されたか
    mock_st7789v.assert_called_once_with(pin=SpiPins(rst=25, dc=24, bl=23))
    # dispoff が呼ばれたか
    mock_lcd.dispoff.assert_called_once()


def test_off_help():
    """'off' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(off, ["--help"])
    assert result.exit_code == 0
    assert "off" in result.output
    assert "--rst" in result.output
    assert "--dc" in result.output
    assert "--bl" in result.output
