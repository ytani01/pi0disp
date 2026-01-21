#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for interactive orientation wizard."""

from unittest.mock import MagicMock, patch
from pi0disp.commands.lcd_check import run_orientation_wizard

@patch("pi0disp.commands.lcd_check.draw_lcd_test_pattern")
@patch("pi0disp.commands.lcd_check.update_toml_settings")
def test_run_orientation_wizard_loop(mock_update, mock_draw):
    """Verify key inputs change rotation and use standard test pattern."""
    disp = MagicMock()
    disp.size.width = 240
    disp.size.height = 320
    disp.rotation = 0
    
    # a (0), b (90), ENTER (confirm) の入力をシミュレート
    with patch("click.getchar", side_effect=["a", "b", "\r"]):
        res = run_orientation_wizard(disp, debug=False)
        
        # 期待値: 
        # 1. 向き調整に draw_lcd_test_pattern が使われている
        # 2. 確定時に update_toml_settings が呼ばれる
        # 3. 最終的な回転角 90 が返る
        
        assert res == 90
        assert mock_draw.called
        mock_update.assert_called_with({"rotation": 90}, "pi0disp.toml")
        disp.set_rotation.assert_any_call(90)
