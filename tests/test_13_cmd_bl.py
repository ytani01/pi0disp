"""Tests for 'bl' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.bl import bl_cmd


@patch("pi0disp.commands.bl.DispSpi")
def test_bl_success(mock_disp_spi):
    """'bl' コマンドの正常系テスト."""
    mock_lcd = MagicMock()
    mock_disp_spi.return_value.__enter__.return_value = mock_lcd

    runner = CliRunner()
    # 輝度 128 を設定
    result = runner.invoke(bl_cmd, ["128"])

    assert result.exit_code == 0
    mock_lcd.set_brightness.assert_called_once_with(128)


@patch("pi0disp.commands.bl.DispSpi")
def test_bl_clamp(mock_st7789v):
    """'bl' コマンドの値のクランプテスト."""
    mock_lcd = MagicMock()
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    runner = CliRunner()
    # 255 を超える値を指定
    result = runner.invoke(bl_cmd, ["300"])
    assert result.exit_code == 0
    # val = max(0, min(255, val)) なので 255 になるはず
    mock_lcd.set_brightness.assert_called_with(255)

    # 0 未満の値を指定
    result = runner.invoke(bl_cmd, ["--", "-10"])
    assert result.exit_code == 0
    mock_lcd.set_brightness.assert_called_with(0)


def test_bl_help():
    """'bl' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(bl_cmd, ["--help"])
    assert result.exit_code == 0
    assert "set backlight brightness" in result.output
