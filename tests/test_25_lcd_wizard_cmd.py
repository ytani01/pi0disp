#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for 'lcd-check --wizard' command."""

from unittest.mock import MagicMock, patch

import pytest
from pi0disp.commands.lcd_check import lcd_check

@pytest.fixture
def mock_st7789v():
    with patch("pi0disp.commands.lcd_check.ST7789V") as mock_class:
        mock_instance = MagicMock()
        mock_instance.size.width = 320
        mock_instance.size.height = 240
        mock_instance.__enter__.return_value = mock_instance
        mock_class.return_value = mock_instance
        yield mock_instance

def test_lcd_wizard_flow(cli_mock_env, mock_st7789v):
    """ウィザードの正常系フローをテストする."""
    runner, _, _ = cli_mock_env
    
    # isolated_filesystem を使って設定ファイルの書き込みをテスト
    with runner.isolated_filesystem():
        # Q1: black (seen_bg)
        # Q2: red (seen_color)
        # Confirm: y (save)
        # (seen_color の質問文が変更されたので注意)
        result = runner.invoke(lcd_check, ["--wizard"], input="black\nred\ny\n")

        assert result.exit_code == 0
        assert "推定される設定: bgr=False, invert=False" in result.output
        assert "設定を保存しました:" in result.output
        assert "pi0disp.toml" in result.output
        
        # 保存された内容を確認 (パスを抽出して確認)
        import re
        import tomlkit
        match = re.search(r"設定を保存しました: (.*\.toml)", result.output)
        assert match
        save_path = match.group(1)
        
        with open(save_path, "r") as f:
            data = tomlkit.parse(f.read())
        assert data["pi0disp"]["bgr"] is False
        assert data["pi0disp"]["invert"] is False
    
    # init_display が 基準表示(1) + 判定後表示(1) = 2回呼ばれる
    assert mock_st7789v.init_display.call_count == 2


