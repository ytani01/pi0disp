"""Tests for 'bl' command."""

from unittest.mock import MagicMock

from click.testing import CliRunner

from pi0disp.commands.bl import bl_cmd


def test_bl_success(mock_pi_instance):
    """'bl' コマンドの正常系テスト."""

    runner = CliRunner()
    # 輝度 128 を設定
    result = runner.invoke(bl_cmd, ["128"])

    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_called_once_with(23, 128)


def test_bl_clamp(mock_pi_instance):
    """'bl' コマンドの値のクランプテスト."""

    runner = CliRunner()
    # 255 を超える値を指定
    result = runner.invoke(bl_cmd, ["300"])
    assert result.exit_code == 0

    # 0 未満の値を指定
    result = runner.invoke(bl_cmd, ["--", "-10"])
    assert result.exit_code == 0

    assert mock_pi_instance.set_PWM_dutycycle.call_count == 2
    mock_pi_instance.set_PWM_dutycycle.assert_any_call(23, 255)
    mock_pi_instance.set_PWM_dutycycle.assert_any_call(23, 0)


def test_bl_help():
    """'bl' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(bl_cmd, ["--help"])
    assert result.exit_code == 0
    assert "Sets the backlight brightness (0-255)." in result.output
