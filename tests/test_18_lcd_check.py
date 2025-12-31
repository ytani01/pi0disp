"""Tests for lcd_check.py sample script."""

import sys
from unittest.mock import MagicMock, patch

# samples ディレクトリをパスに追加
sys.path.append("samples")


@patch("pi0disp.disp.st7789v.ST7789V")
@patch("builtins.input", side_effect=["", "", "", ""])  # input() を4回空打ち
@patch("PIL.ImageDraw.Draw")
@patch("PIL.ImageFont.truetype")
@patch("PIL.ImageFont.load_default")
def test_lcd_check_execution(
    mock_load_default, mock_truetype, mock_draw, mock_input, mock_st7789v
):
    """lcd_check.py がエラーなく実行されることをテスト."""
    import lcd_check  # type: ignore[import-not-found]

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
    lcd_check.main()

    # 期待される動作の検証
    assert mock_st7789v.called
    assert mock_disp.display.call_count == 4  # 4つのテストパターン
    assert mock_disp.init_display.call_count == 4
    assert mock_draw_instance.text.called  # テキストが描画されたこと
    assert mock_disp.close.called
