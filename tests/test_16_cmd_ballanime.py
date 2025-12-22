"""Tests for 'ballanime' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.ballanime import ballanime


@patch("pi0disp.commands.ballanime.ST7789V")
@patch("time.sleep")
def test_ballanime_success(mock_sleep, mock_st7789v_patch, cli_mock_env):
    """'ballanime' コマンドの正常系テスト."""
    runner, mock_pi_instance, _ = cli_mock_env

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

    # 無限ループを止める
    mock_sleep.side_effect = KeyboardInterrupt("Stop loop")

    runner = CliRunner()
    # --num-balls を使用
    result = runner.invoke(ballanime, ["--num-balls", "1"])

    # KeyboardInterrupt で抜けた場合は exit_code 0 (捕まえて正常終了しているため)
    assert result.exit_code == 0
    assert mock_lcd.display.called


def test_ballanime_help(cli_mock_env):
    """'ballanime' コマンドのヘルプ表示テスト."""
    runner, _, _ = cli_mock_env
    result = runner.invoke(ballanime, ["--help"])
    assert result.exit_code == 0
    assert "Balls animation" in result.output
