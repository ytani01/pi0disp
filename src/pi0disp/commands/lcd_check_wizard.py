#
# (c) 2026 Yoichi Tanibayashi
#
"""LCD Interactive Wizard components."""

from dataclasses import dataclass
import click
from ..utils.mylogger import get_logger
from ..utils.lcd_test_pattern import draw_lcd_test_pattern

@dataclass
class WizardState:
    """Holds the current state of LCD settings."""
    rotation: int = 0
    invert: bool = False
    bgr: bool = False
    x_offset: int = 0
    y_offset: int = 0

    def update_by_key(self, key: str) -> bool:
        """Update state based on key input. Returns True if handled."""
        key = key.lower()
        if key == "a":
            self.rotation = 0
        elif key == "b":
            self.rotation = 90
        elif key == "c":
            self.rotation = 180
        elif key == "d":
            self.rotation = 270
        elif key == "i":
            self.invert = not self.invert
        elif key == "g":
            self.bgr = not self.bgr
        elif key == "h":
            self.x_offset -= 1
        elif key == "l":
            self.x_offset += 1
        elif key == "k":
            self.y_offset -= 1
        elif key == "j":
            self.y_offset += 1
        else:
            return False
        return True

    def to_dict(self) -> dict:
        return {
            "rotation": self.rotation,
            "invert": self.invert,
            "bgr": self.bgr,
            "x_offset": self.x_offset,
            "y_offset": self.y_offset,
        }
    
    def copy(self):
        return WizardState(
            rotation=self.rotation,
            invert=self.invert,
            bgr=self.bgr,
            x_offset=self.x_offset,
            y_offset=self.y_offset
        )

class WizardUI:
    """Base interface for Wizard UI handling."""
    def get_key(self) -> str:
        raise NotImplementedError()
    
    def show_status(self, state: WizardState):
        raise NotImplementedError()

class ClickWizardUI(WizardUI):
    """Real implementation of WizardUI using click and console."""
    def get_key(self) -> str:
        return click.getchar()
    
    def show_status(self, state: WizardState):
        status = f"Rot:{state.rotation:3} Inv:{str(state.invert):5} BGR:{str(state.bgr):5} Off:({state.x_offset},{state.y_offset})"
        print(f"\rCurrent: {status} (a-d,i,g,hjkl,ENTER,q) ", end="", flush=True)

class LCDWizard:
    """Manages the wizard flow."""
    def __init__(self, disp, ui: WizardUI, debug: bool = False):
        self.disp = disp
        self.ui = ui
        self.__log = get_logger(__name__, debug)
        self.state = WizardState(
            rotation=disp.rotation,
            invert=disp._invert,
            bgr=disp._bgr,
            x_offset=disp._x_offset,
            y_offset=disp._y_offset
        )

    def run(self) -> dict:
        """Run the interactive loop."""
        print("\n--- LCD Interactive Wizard ---")
        # (Help messages omitted for brevity in this initial implementation)

        while True:
            # Update hardware
            self.disp._invert = self.state.invert
            self.disp._bgr = self.state.bgr
            self.disp._x_offset = self.state.x_offset
            self.disp._y_offset = self.state.y_offset
            self.disp.init_display()
            self.disp.set_rotation(self.state.rotation)

            # Draw test pattern
            width, height = self.disp.size.width, self.disp.size.height
            self.disp._last_image = None # Force clear
            img = draw_lcd_test_pattern(width, height, self.state.invert, self.state.bgr)
            self.disp.display(img, full=True)

            self.ui.show_status(self.state)

            key = self.ui.get_key().lower()
            if key in ["\r", "\n"]:
                print("\n設定を確定しました。")
                break
            elif key == "q":
                print("\n中断しました。")
                raise click.Abort()
            
            self.state.update_by_key(key)

        return self.state.to_dict()
