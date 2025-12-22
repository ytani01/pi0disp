"""Tests for 'bl' command."""

from click.testing import CliRunner

from pi0disp.commands.bl import bl_cmd
from pi0disp.disp.disp_conf import DispConf


def test_bl_success(mock_pi_instance):
    """'bl' コマンドの正常系テスト."""
    conf = DispConf()
    bl_pin = conf.data.spi.bl

    runner = CliRunner()
    # 輝度 128 を設定
    result = runner.invoke(bl_cmd, ["128"])

    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_called_once_with(bl_pin, 128)


def test_bl_clamp(mock_pi_instance):
    """'bl' コマンドの値のクランプテスト."""
    conf = DispConf()
    bl_pin = conf.data.spi.bl

    runner = CliRunner()
    # 255 を超える値を指定
    result = runner.invoke(bl_cmd, ["300"])
    assert result.exit_code == 0

    # 0 未満の値を指定
    result = runner.invoke(bl_cmd, ["--", "-10"])
    assert result.exit_code == 0

    assert mock_pi_instance.set_PWM_dutycycle.call_count == 2
    mock_pi_instance.set_PWM_dutycycle.assert_any_call(bl_pin, 255)
    mock_pi_instance.set_PWM_dutycycle.assert_any_call(bl_pin, 0)


def test_bl_help():
    """'bl' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(bl_cmd, ["--help"])
    assert result.exit_code == 0
    assert "Sets the backlight brightness (0-255)." in result.output


def test_bl_option(mock_pi_instance):
    """'bl' コマンドの --bl オプションのテスト."""
    bl_pin = 15
    brightness = 128

    runner = CliRunner()
    result = runner.invoke(bl_cmd, ["--bl", str(bl_pin), str(brightness)])

    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_called_once_with(
        bl_pin, brightness
    )


def test_bl_option_with_zero(mock_pi_instance):
    """'bl' コマンドの --bl オプションに0を指定した場合のテスト."""
    # bl.pyのコードの制限により、--bl 0を指定すると設定ファイルの値が使われる
    # このテストはその挙動を検証する
    brightness = 100

    runner = CliRunner()
    result = runner.invoke(bl_cmd, ["--bl", "0", str(brightness)])
    assert result.exit_code == 0
    assert "no backlight: do nothing" in result.output
