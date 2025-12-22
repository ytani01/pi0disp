import pytest
from click.testing import CliRunner

from pi0disp.commands.bl import bl_cmd


def test_config_nonzero(cli_mock_env):
    """設定ファイルで bl が 0 以外の値の場合."""
    runner, mock_pi_instance, mock_dynaconf = cli_mock_env
    bl_pin = 23
    brightness = 128
    mock_dynaconf.get.return_value.spi.bl = bl_pin  # Configured bl_pin

    result = runner.invoke(bl_cmd, [str(brightness)])
    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_called_once_with(
        bl_pin, brightness
    )


def test_config_zero(cli_mock_env):
    """設定ファイルで bl が 0 の場合 (何もしない)."""
    runner, mock_pi_instance, mock_dynaconf = cli_mock_env
    brightness = 128
    mock_dynaconf.get.return_value.spi.bl = 0  # Configured bl_pin as 0

    result = runner.invoke(bl_cmd, [str(brightness)])
    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()


def test_option_nonzero(cli_mock_env):
    """--bl オプションで 0 以外の値を指定した場合."""
    runner, mock_pi_instance, mock_dynaconf = cli_mock_env
    bl_pin = 15
    brightness = 128
    # オプション指定時は設定ファイルの値は使われないことを確認するため、設定は異なる値に
    mock_dynaconf.get.return_value.spi.bl = 23

    result = runner.invoke(bl_cmd, ["--bl", str(bl_pin), str(brightness)])
    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_called_once_with(
        bl_pin, brightness
    )


def test_option_zero(cli_mock_env):
    """--bl オプションで 0 を指定した場合 (何もしない)."""
    runner, mock_pi_instance, mock_dynaconf = cli_mock_env
    brightness = 100
    # オプション指定時は設定ファイルの値は使われないことを確認するため、設定は異なる値に
    mock_dynaconf.get.return_value.spi.bl = 23

    result = runner.invoke(bl_cmd, ["--bl", "0", str(brightness)])
    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()
    assert "no backlight: do nothing" in result.output


@pytest.mark.parametrize(
    "input_args, expected_dutycycle",
    [
        (["300"], 255),  # 255を超える値を指定した場合
        (["--", "-10"], 0),  # 0未満の値を指定した場合
    ],
)
def test_clamp_with_config(cli_mock_env, input_args, expected_dutycycle):
    """値のクランプテスト (設定ファイル使用)."""
    runner, mock_pi_instance, mock_dynaconf = cli_mock_env
    bl_pin = 23
    mock_dynaconf.get.return_value.spi.bl = bl_pin

    result = runner.invoke(bl_cmd, input_args)
    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_called_once_with(
        bl_pin, expected_dutycycle
    )


def test_config_zero_from_conf(cli_mock_env):
    """設定ファイルで bl が 0 の場合（bl is Noneパス経由で何もしない）."""
    runner, mock_pi_instance, mock_dynaconf = cli_mock_env
    brightness = 100
    mock_dynaconf.get.return_value.spi.bl = 0  # Configured bl_pin as 0

    result = runner.invoke(bl_cmd, [str(brightness)])
    assert result.exit_code == 0
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()
    assert "no backlight: do nothing" in result.output


def test_pigpio_connection_failure(cli_mock_env):
    """pigpioデーモンに接続できない場合のエラーハンドリング."""
    runner, mock_pi_instance, mock_dynaconf = cli_mock_env
    bl_pin = 23
    brightness = 128
    mock_dynaconf.get.return_value.spi.bl = bl_pin
    mock_pi_instance.connected = False  # 接続失敗をシミュレート

    result = runner.invoke(bl_cmd, [str(brightness)], catch_exceptions=False)
    assert result.exit_code == 0
    assert "Could not connect to pigpio daemon. Is it running?" in result.output
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()
    mock_pi_instance.stop.assert_called_once()  # finallyブロックでstopが呼ばれることを確認


def test_help_message():
    """ヘルプメッセージ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(bl_cmd, ["--help"])
    assert result.exit_code == 0
    assert "Sets the backlight brightness (0-255)." in result.output
