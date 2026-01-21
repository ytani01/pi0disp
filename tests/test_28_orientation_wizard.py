#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for interactive orientation wizard."""

from unittest.mock import MagicMock, patch
from pi0disp.commands.lcd_check import run_orientation_wizard

def test_run_orientation_wizard_loop():
    """Verify key inputs change rotation and re-draw."""
    disp = MagicMock()
    disp.size.width = 240
    disp.size.height = 320
    disp.rotation = 0
    conf = MagicMock()
    
    # a (0), b (90), ENTER (confirm) の入力をシミュレート
    with patch("click.getchar", side_effect=["a", "b", "\r"]):
        res = run_orientation_wizard(disp, debug=False)
        
        # 期待値: 
        # 1. 'a' で set_rotation(0) が呼ばれる
        # 2. 'b' で set_rotation(90) が呼ばれる
        # 3. 各操作で display が呼ばれる
        # 4. 最終的な回転角 90 が返る
        
        assert res == 90
        disp.set_rotation.assert_any_call(0)
        disp.set_rotation.assert_any_call(90)
        assert disp.display.call_count >= 2
