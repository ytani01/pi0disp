"""Tests for 'rgb' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.rgb import rgb


@patch("pi0disp.commands.rgb.ST7789V")
@patch("time.sleep")
def test_rgb_success(mock_sleep, mock_st7789v):
    """'rgb' コマンドの正常系テスト（1ループで終了させる）."""
    mock_lcd = MagicMock()
    mock_lcd.size.width = 240
    mock_lcd.size.height = 320
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    # ループ内で time.sleep が呼ばれる前に KeyboardInterrupt が発生すると、
    # display() が呼ばれない可能性がある。
    # ここでは、確実に1回は sleep(None) を通るように side_effect を設定している。
    mock_sleep.side_effect = [None, KeyboardInterrupt("Stop loop")]

    runner = CliRunner()
    result = runner.invoke(rgb, ["--duration", "0.1"])

    # KeyboardInterrupt で抜けた場合
    assert result.exit_code in [0, 1]
    assert mock_lcd.display.called


def test_rgb_help():
    """'rgb' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(rgb, ["--help"])
    assert result.exit_code == 0
    assert "RGB Circles" in result.output
