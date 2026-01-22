#
# (c) 2026 Yoichi Tanibayashi
#
"""Red tests for refactored LCD Wizard."""

from unittest.mock import MagicMock

# These will be the new components
# from pi0disp.commands.lcd_check_wizard import LCDWizard, WizardState, WizardUI


def test_wizard_state_update():
    """Test that WizardState correctly updates its values."""
    from pi0disp.commands.lcd_check_wizard import WizardState

    state = WizardState(
        rotation=90, invert=False, bgr=False, x_offset=0, y_offset=0
    )

    state.update_by_key("a")
    assert state.rotation == 0

    state.update_by_key("i")
    assert state.invert is True

    state.update_by_key("l")
    assert state.x_offset == 1


def test_wizard_logic_flow():
    """Test the wizard's logic flow without actual display or getchar."""
    from pi0disp.commands.lcd_check_wizard import LCDWizard, WizardUI

    class MockUI(WizardUI):
        def __init__(self, keys):
            self.keys = keys
            self.index = 0
            self.outputs = []

        def get_key(self):
            k = self.keys[self.index]
            self.index += 1
            return k

        def show_status(self, state):
            self.outputs.append(state.copy())

        def show_help(self):
            pass

    disp = MagicMock()
    disp.size.width = 240
    disp.size.height = 320
    disp.rotation = 90
    disp._invert = False
    disp._bgr = False
    disp._x_offset = 0
    disp._y_offset = 0

    ui = MockUI(["a", "i", "\r"])
    wizard = LCDWizard(disp, ui)

    result = wizard.run()

    assert result["rotation"] == 0
    assert result["invert"] is True
    assert len(ui.outputs) >= 3  # Initial + 2 changes + Final
