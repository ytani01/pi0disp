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
        # Ensure size returns real integers for formatting
        mock_instance.size.width = 320
        mock_instance.size.height = 240
        mock_instance.rotation = 90
        mock_instance._invert = False
        mock_instance._bgr = False
        mock_instance._x_offset = 0
        mock_instance._y_offset = 0
        mock_instance.__enter__.return_value = mock_instance
        mock_class.return_value = mock_instance
        yield mock_instance


def test_lcd_wizard_flow(cli_mock_env, mock_st7789v):
    """ウィザードの正常系フローをテストする."""
    runner, _, _ = cli_mock_env

    # isolated_filesystem を使って設定ファイルの書き込みをテスト
    with runner.isolated_filesystem():
        # Unified Wizard input:
        # ENTER (\r): confirm default settings (rot=90, inv=False, bgr=False)
        # y: confirm save
        result = runner.invoke(lcd_check, ["--wizard"], input="\r\ny\n")

        assert result.exit_code == 0
        assert "設定を確定しました。" in result.output
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
        table = data.get("pi0disp", {})
        assert table.get("bgr") is False
        assert table.get("invert") is False
        assert table.get("rotation") == 90

    # init_display がループの各ステップで呼ばれる
    assert mock_st7789v.init_display.call_count >= 1
