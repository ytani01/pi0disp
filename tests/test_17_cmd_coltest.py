"""Tests for 'coltest' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.coltest import coltest


@patch("pi0disp.commands.coltest.ST7789V")
@patch("pi0disp.commands.coltest.input")
@patch("pi0disp.commands.coltest.readline")
@patch("os.path.exists")
def test_coltest_success(
    mock_exists, mock_readline, mock_input, mock_st7789v
):
    """'coltest' コマンドの正常系テスト."""
    mock_exists.return_value = False
    mock_lcd = MagicMock()
    mock_lcd.size.width = 240
    mock_lcd.size.height = 320
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    # コマンド入力をシミュレート: r128, その後クイット（q）
    mock_input.side_effect = ["r128", "q"]

    runner = CliRunner()
    result = runner.invoke(coltest)

    assert result.exit_code == 0
    # 初期描画と更新で2回呼ばれるはず
    assert mock_lcd.display.call_count == 2


def test_coltest_help():
    """'coltest' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(coltest, ["--help"])
    assert result.exit_code == 0
    assert "Interactive Color Test" in result.output
