"""Tests for simple_drawing.py sample script."""

import sys
from unittest.mock import MagicMock, patch

# samples ディレクトリをパスに追加
sys.path.append("samples")


@patch("pi0disp.disp.st7789v.ST7789V")
@patch("time.sleep")  # sleep をモックしてテスト時間を短縮
@patch("PIL.ImageDraw.Draw")
@patch("PIL.ImageFont.truetype")
@patch("PIL.ImageFont.load_default")
def test_simple_drawing_execution(
    mock_load_default, mock_truetype, mock_draw, mock_sleep, mock_st7789v
):
    """simple_drawing.py がエラーなく実行されることをテスト."""
    import simple_drawing  # type: ignore[import-not-found]

    # モックの設定
    mock_disp = MagicMock()
    mock_disp.size.width = 320
    mock_disp.size.height = 240
    mock_disp.rotation = 90
    mock_st7789v.return_value = mock_disp

    # ImageDraw.Draw のモック
    mock_draw_instance = MagicMock()
    mock_draw.return_value = mock_draw_instance

    # フォントのモック
    mock_truetype.return_value = MagicMock()
    mock_load_default.return_value = MagicMock()

    # main 実行
    simple_drawing.main()

    # 期待される動作の検証
    assert mock_st7789v.called
    assert mock_disp.display.called
    assert mock_draw_instance.rectangle.called
    assert mock_draw_instance.ellipse.called
    assert mock_draw_instance.line.called
    assert mock_draw_instance.text.called
    assert mock_sleep.called
    assert mock_sleep.call_args[0][0] == 5  # 5秒間待機したか
    assert mock_disp.close.called
