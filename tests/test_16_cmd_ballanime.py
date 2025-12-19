"""Tests for 'ballanime' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.ballanime import ballanime


@patch("pi0disp.commands.ballanime.ST7789V")
@patch("time.sleep")
def test_ballanime_success(mock_sleep, mock_st7789v):
    """'ballanime' コマンドの正常系テスト."""
    mock_lcd = MagicMock()
    mock_lcd.size.width = 240
    mock_lcd.size.height = 320
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    # 無限ループを止める
    mock_sleep.side_effect = KeyboardInterrupt("Stop loop")

    runner = CliRunner()
    # --num-balls を使用
    result = runner.invoke(ballanime, ["--num-balls", "1"])

    # KeyboardInterrupt で抜けた場合は exit_code 0 (捕まえて正常終了しているため)
    assert result.exit_code == 0
    assert mock_lcd.display.called


def test_ballanime_help():
    """'ballanime' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(ballanime, ["--help"])
    assert result.exit_code == 0
    assert "Balls animation" in result.output
