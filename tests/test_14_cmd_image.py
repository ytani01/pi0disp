"""Tests for 'image' command."""

import traceback
from unittest.mock import MagicMock, patch

from click.testing import CliRunner

from pi0disp.commands.image import image


@patch("pi0disp.commands.image.ST7789V")
@patch("pi0disp.commands.image.Image.open")
@patch("pi0disp.commands.image.ImageProcessor")
def test_image_success(
    mock_processor_cls, mock_img_open, mock_st7789v, tmp_path
):
    """'image' コマンドの正常系テスト."""
    mock_lcd = MagicMock()
    mock_lcd.size.width = 240
    mock_lcd.size.height = 320
    mock_st7789v.return_value.__enter__.return_value = mock_lcd

    mock_img = MagicMock()
    mock_img_open.return_value = mock_img

    mock_processor = mock_processor_cls.return_value
    mock_processor.resize_with_aspect_ratio.return_value = mock_img
    mock_processor.apply_gamma.return_value = mock_img

    # 一時的な画像ファイルを作成
    img_file = tmp_path / "dummy.png"
    img_file.touch()

    runner = CliRunner()
    # sys.modules を辞書としてパッチする（一部のみ）
    with patch.dict("sys.modules", {"cairosvg": MagicMock()}):
        result = runner.invoke(image, [str(img_file), "--duration", "0.01"])

    if result.exit_code != 0:
        print(f"EXIT CODE: {result.exit_code}")
        print(f"OUTPUT:\n{result.output}")
        if result.exception:
            print("EXCEPTION TRACEBACK:")
            traceback.print_exception(
                type(result.exception),
                result.exception,
                result.exception.__traceback__,
            )

    assert result.exit_code == 0
    # display が呼ばれたことを確認
    assert mock_lcd.display.called


def test_image_not_found():
    """'image' コマンドのファイル未見時テスト."""
    runner = CliRunner()
    result = runner.invoke(image, ["nonexistent.png"])

    # click の引数チェック(exists=True)で失敗する場合、exit_code 2
    assert result.exit_code != 0


def test_image_help():
    """'image' コマンドのヘルプ表示テスト."""
    runner = CliRunner()
    result = runner.invoke(image, ["--help"])
    assert result.exit_code == 0
    assert "Displays an image" in result.output
