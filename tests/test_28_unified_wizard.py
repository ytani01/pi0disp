#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for unified interactive LCD wizard."""

from unittest.mock import MagicMock, patch

from pi0disp.commands.lcd_check_wizard import LCDWizard, ClickWizardUI

@patch("pi0disp.commands.lcd_check_wizard.draw_lcd_test_pattern")
def test_lcd_wizard_loop(mock_draw):
    """Verify key inputs change rotation, invert, bgr via LCDWizard."""
    disp = MagicMock()
    disp.size.width = 240
    disp.size.height = 320
    disp.rotation = 90
    disp._invert = False
    disp._bgr = False
    disp._last_image = MagicMock()
    disp._x_offset = 0
    disp._y_offset = 0

    ui = ClickWizardUI()

    # 1. 'a' (0°), 2. 'i' (invert=True), 3. 'g' (bgr=True), 4. ENTER (confirm)
    with patch("click.getchar", side_effect=["a", "i", "g", "\r"]):
        wiz = LCDWizard(disp, ui)
        res = wiz.run()

        assert res == {
            "rotation": 0,
            "invert": True,
            "bgr": True,
            "x_offset": 0,
            "y_offset": 0,
        }

        # 設定変更ごとに _last_image = None が設定されているはず
        assert disp._last_image is None
        assert disp._invert is True
        assert disp._bgr is True

        # 設定変更ごとに _last_image = None が設定されているはず
        assert disp._last_image is None

        # 各種設定変更メソッドが呼ばれていること
        disp.set_rotation.assert_any_call(0)
        assert disp._invert is True
        assert disp._bgr is True

        # 描画が呼ばれていること
        assert mock_draw.called
        assert disp.display.called
