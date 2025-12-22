"""Tests for 'coltest' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.coltest import coltest


@patch("pi0disp.commands.coltest.ST7789V")
@patch("pi0disp.commands.coltest.input")
@patch("pi0disp.commands.coltest.readline")
@patch("os.path.exists")
def test_coltest_success(
    mock_exists, mock_readline, mock_input, mock_st7789v_patch, cli_mock_env
):
    """'coltest' コマンドの正常系テスト."""
    runner, mock_pi_instance, _ = cli_mock_env

    mock_exists.return_value = False
    mock_lcd = MagicMock()
    mock_lcd.size.width = 240
    mock_lcd.size.height = 320
    # mock_st7789v_patch の設定で mock_pi_instance を利用 (ただし ST7789V の初期化時に pi インスタンスが渡されると仮定)
    mock_st7789v_patch.return_value.__enter__.return_value = mock_lcd
    mock_st7789v_patch.return_value.side_effect = (
        lambda pi_instance=mock_pi_instance,
        *args,
        **kwargs: mock_st7789v_patch.return_value
    )

    # コマンド入力をシミュレート: r128, その後クイット（q）
    mock_input.side_effect = ["r128", "q"]

    runner = CliRunner()
    result = runner.invoke(coltest)

    assert result.exit_code == 0
    # 初期描画と更新で2回呼ばれるはず
    assert mock_lcd.display.call_count == 2


def test_coltest_help(cli_mock_env):
    """'coltest' コマンドのヘルプ表示テスト."""
    runner, _, _ = cli_mock_env
    result = runner.invoke(coltest, ["--help"])
    assert result.exit_code == 0
    assert "Interactive Color Test" in result.output
