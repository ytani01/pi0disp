"""Tests for 'image' command."""

from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.image import image


@patch("pi0disp.commands.image.ST7789V")
@patch("pi0disp.commands.image.Image.open")
@patch("pi0disp.commands.image.ImageProcessor")
def test_image_success(
    mock_processor_cls,
    mock_img_open,
    mock_st7789v_patch,
    tmp_path,
    cli_mock_env,
):
    """'image' コマンドの正常系テスト."""
    runner, mock_pi_instance, _ = cli_mock_env

    mock_lcd = MagicMock()
    mock_lcd.size.width = 240
    mock_lcd.size.height = 320
    # mock_st7789v_patch の設定で mock_pi_instance を利用 (ただし ST7789V の初期化時に pi インスタンスが渡されると仮定)
    # ここでは、mock_st7789v_patch は ST7789V クラス自体をモックしているので、
    # そのインスタンスが返るように設定し、そのインスタンスに __enter__ メソッドを追加
    mock_st7789v_patch.return_value.__enter__.return_value = mock_lcd
    # ST7789V のコンストラクタが呼び出された際の振る舞いを定義する場合
    # ST7789V クラスのコンストラクタに mock_pi_instance を渡すと仮定
    mock_st7789v_patch.return_value.side_effect = (
        lambda pi_instance=mock_pi_instance,
        *args,
        **kwargs: mock_st7789v_patch.return_value
    )


def test_image_not_found():
    """'image' コマンドのファイル未見時テスト."""
    runner = CliRunner()
    result = runner.invoke(image, ["nonexistent.png"])

    # click の引数チェック(exists=True)で失敗する場合、exit_code 2
    assert result.exit_code != 0


def test_image_help(cli_mock_env):
    """'image' コマンドのヘルプ表示テスト."""
    runner, _, _ = cli_mock_env
    result = runner.invoke(image, ["--help"])
    assert result.exit_code == 0
    assert "Displays an image" in result.output
