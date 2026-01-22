#
# (c) 2026 Yoichi Tanibayashi
#
"""LCD Interactive Wizard components."""

from typing import Any

import click

from ..utils.lcd_test_pattern import draw_lcd_test_pattern
from ..utils.mylogger import get_logger


class SettingItem:
    """Base class for a display setting item."""

    def __init__(self, name: str, value: Any, keys: dict[str, Any]):
        self.name = name
        self.value = value
        self.keys = keys

    def update(self, key: str) -> bool:
        if key in self.keys:
            self.value = self.keys[key]
            return True
        return False


class ToggleSettingItem(SettingItem):
    """Setting item that toggles between True and False."""

    def __init__(self, name: str, value: bool, key: str):
        super().__init__(name, value, {key: None})
        self.toggle_key = key

    def update(self, key: str) -> bool:
        if key == self.toggle_key:
            self.value = not self.value
            return True
        return False


class OffsetSettingItem(SettingItem):
    """Setting item for X/Y offsets."""

    def __init__(self, name: str, value: int, dec_key: str, inc_key: str):
        super().__init__(name, value, {dec_key: -1, inc_key: 1})
        self.dec_key = dec_key
        self.inc_key = inc_key

    def update(self, key: str) -> bool:
        if key == self.dec_key:
            self.value -= 1
            return True
        elif key == self.inc_key:
            self.value += 1
            return True
        return False


class WizardState:
    """Holds the current state of LCD settings using items."""

    def __init__(
        self, rotation=0, invert=False, bgr=False, x_offset=0, y_offset=0
    ):
        self.items = [
            SettingItem(
                "rotation", rotation, {"a": 0, "b": 90, "c": 180, "d": 270}
            ),
            ToggleSettingItem("invert", invert, "i"),
            ToggleSettingItem("bgr", bgr, "g"),
            OffsetSettingItem("x_offset", x_offset, "h", "l"),
            OffsetSettingItem("y_offset", y_offset, "k", "j"),
        ]

    @property
    def rotation(self) -> int:
        return self._get("rotation", 0)

    @property
    def invert(self) -> bool:
        return self._get("invert", False)

    @property
    def bgr(self) -> bool:
        return self._get("bgr", False)

    @property
    def x_offset(self) -> int:
        return self._get("x_offset", 0)

    @property
    def y_offset(self) -> int:
        return self._get("y_offset", 0)

    def _get(self, name: str, default: Any) -> Any:
        for item in self.items:
            if item.name == name:
                return item.value
        return default

    def update_by_key(self, key: str) -> bool:
        for item in self.items:
            if item.update(key):
                return True
        return False

    def to_dict(self) -> dict:
        return {item.name: item.value for item in self.items}

    def copy(self):
        d = self.to_dict()
        return WizardState(**d)


class WizardUI:
    """Base interface for Wizard UI handling."""

    def get_key(self) -> str:
        raise NotImplementedError()

    def show_status(self, state: WizardState):
        raise NotImplementedError()

    def show_help(self):
        raise NotImplementedError()


class ClickWizardUI(WizardUI):
    """Real implementation of WizardUI using click and console."""

    def get_key(self) -> str:
        return click.getchar()

    def show_status(self, state: WizardState):
        status = f"Rot:{state.rotation:3} Inv:{str(state.invert):5} BGR:{str(state.bgr):5} Off:({state.x_offset},{state.y_offset})"
        print(
            f"\rCurrent: {status} (a-d,i,g,hjkl,ENTER,q) ", end="", flush=True
        )

    def show_help(self):
        print("\n--- LCD Interactive Wizard ---")
        print("実機の表示を確認しながら、以下のキーで調整してください。")
        print(
            "背景が『漆黒』、上から『赤・緑・青』の順に見えるのが正解です。"
        )
        print("\n  a, b, c, d : 画面の向き (0°, 90°, 180°, 270°)")
        print("  i          : 色反転 (Invert) ON/OFF")
        print("  g          : 色順序 (BGR) ON/OFF")
        print("  h, j, k, l : 表示位置の微調整 (x_offset, y_offset)")
        print("  ENTER      : この設定で保存して終了")
        print("  q          : 中断")
        print("------------------------------")


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
            y_offset=disp._y_offset,
        )

    def run(self) -> dict:
        """Run the interactive loop."""
        self.ui.show_help()

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
            self.disp._last_image = None  # Force clear
            img = draw_lcd_test_pattern(
                width, height, self.state.invert, self.state.bgr
            )
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
