#
# (c) 2025 Yoichi Tanibayashi
#
"""
ロボットの顔のアニメーション
"""

from __future__ import annotations

import math
import random
import socket

# import sys
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, replace

# from typing import Callable
import click
from PIL import Image, ImageDraw, ImageOps

from pi0disp import __version__, click_common_opts, errmsg, get_logger

# ディスプレイ制御用
try:
    from pi0disp import ST7789V

    HAS_LCD = True
except ImportError:
    HAS_LCD = False

# PCプレビュー用 (OpenCV)
try:
    import cv2
    import numpy as np

    HAS_OPENCV = True
except ImportError:
    HAS_OPENCV = False


class DisplayBase(ABC):
    """ディスプレイ出力を抽象化するクラス"""

    def __init__(self, width, heigtht, debug=False):
        """Constructor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("(abstract)")

        self._width = width
        self._height = heigtht

    @property
    def width(self):
        """Property: width."""
        return self._width

    @property
    def height(self):
        """Property: height."""
        return self._height

    @abstractmethod
    def show_face_parts(self, pil_image):
        """顔のパーツを描画"""
        pass

    @abstractmethod
    def show_face_outline(self, pil_image):
        """画像をデバイスに転送"""
        pass

    @abstractmethod
    def close(self):
        """リソース解放"""
        pass


class Lcd(DisplayBase):
    """LCD Display (ST7789V)."""

    def __init__(self, width, height, debug=False):
        super().__init__(width, height, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)

        if not self._check_pigpio():
            msg = "no pigpiod"
            self.__log.warning(msg)
            raise RuntimeError(msg)

        try:
            self.lcd = ST7789V(
                rotation=270, bgr=False, invert=True, debug=debug
            )
            # self.lcd.set_rotation(270)
        except Exception as e:
            self.__log.error(errmsg(e))
            raise RuntimeError(errmsg(e))

        self.__log.debug("Found LCD, returning Lcd.")

    def _check_pigpio(self, host="localhost", port=8888, timeout=0.1):
        """pigpioデーモンの存在確認"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def show_face_outline(self, pil_image):
        """Show all."""
        self.__log.debug("")
        self.lcd.display(pil_image)

    def show_face_parts(self, pil_image):
        """Show face parts."""
        self.lcd.display_region(pil_image, 41, 50, 105, 138)
        self.lcd.display_region(pil_image, 150, 50, 215, 138)
        self.lcd.display_region(pil_image, 89, 135, 170, 200)

    def close(self):
        self.lcd.close(True)


class CV2Disp(DisplayBase):
    """OpenCV."""

    def __init__(self, width, height, debug=False):
        super().__init__(width, height, debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("initialized CV2Disp")

    def _show(self, pil_image):
        frame = np.array(pil_image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Robot Face", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            raise KeyboardInterrupt("ESC pressed")

    def show_face_outline(self, pil_image):
        self._show(pil_image)

    def show_face_parts(self, pil_image):
        """Show face parts."""
        self._show(pil_image)

    def close(self):
        cv2.destroyAllWindows()


def get_disp_dev(width, height, debug=False) -> DisplayBase:
    """Create display device."""
    _log = get_logger("()", debug)

    if HAS_LCD:
        try:
            return Lcd(width, height, debug=debug)
        except Exception as e:
            _log.error(errmsg(e))

    if HAS_OPENCV:
        _log.warning("Found OpenCV, returning CV2Disp.")
        return CV2Disp(width, height, debug=debug)
    _log.warning("警告: 表示可能なデバイスがありません (コンソール実行のみ)")
    raise RuntimeError("No suitable display display device found.")


# ===========================================================================
# 顔の状態
# ===========================================================================


@dataclass
class BrowState:
    tilt: float = 0.0


@dataclass
class EyeState:
    open: float = 1.0  # 0.0 ～ 1.0
    size: float = 8.0
    curve: float = 0.0


@dataclass
class MouthState:
    curve: float = 0.0  # +20(笑顔) ～ -20(への字)
    open: float = 0.0  # 0.0 ～ 1.0


@dataclass
class FaceState:
    brow: BrowState = field(default_factory=BrowState)
    left_eye: EyeState = field(default_factory=EyeState)
    right_eye: EyeState = field(default_factory=EyeState)
    mouth: MouthState = field(default_factory=MouthState)

    def copy(self) -> "FaceState":
        """Create a copy of this FaceState."""
        return replace(self)


# ===========================================================================
# 設定セクション
# ===========================================================================

BROW_MAP: dict[str, int] = {"v": 25, "_": 0, "^": -10}
EYE_MAP: dict[str, dict[str, float]] = {
    "O": {"size": 9.0, "open": 1.0, "curve": 0.0},
    "o": {"size": 6.0, "open": 1.0, "curve": 0.0},
    "_": {"size": 0.0, "open": 0.0, "curve": 0.0},
    "^": {"size": 0.0, "open": 0.0, "curve": 1.0},
    "v": {"size": 0.0, "open": 0.0, "curve": -1.0},
}
MOUTH_MAP: dict[str, dict[str, float]] = {
    "v": {"open": 0.0, "curve": 10},
    "_": {"open": 0.0, "curve": 0},
    "^": {"open": 0.0, "curve": -10},
    "O": {"open": 1.1, "curve": 0},
    "o": {"open": 0.85, "curve": 0},
}

FACE_WORDS = {
    "neutral": "_OO_",
    "zen": "____",
    "happy": "_OOv",
    "smily": "_^^v",
    "sad": "^oo^",
    "angry": "voo^",
    "wink-r": "_O^v",
    "wink-l": "_^Ov",
    "sleepy": "_vvv",
    "surprised": "_ooO",
    "kiss": "_vvo",
}

# レイアウト定数 (顔のパーツの相対座標)
LAYOUT = {
    # 眉
    "brow_offset_y": -15,  # 目のY座標からのオフセット
    "brow_offset_x": 10,
    "brow_offset_y_factor": 10,
    # 目
    "eye_offset": 27,
    "eye_y": 45,
    "eye_line_offset_x": 10,
    "eye_bezier_offset_y": 6,
    # 口
    "mouth_cy": 70,
    "mouth_width": 30,
    "mouth_open_radius_factor": 8,
    "mouth_curve_half_width": 15,
}

# アニメーション定数
ANIMATION = {
    "frame_interval": 0.1,
    "eye_open_threshold": 6,
    "mouth_open_threshold": 0.5,
    "mouth_aspect_ratio": 1.3,
    "face_change_duration": 0.9,
    "gaze_loop_duration": 3.0,
    "gaze_lerp_factor": 0.5,
}

# カラー定数
COLORS: dict[str, str | tuple[int, int, int]] = {
    "line": "black",
    "face_bg": (255, 255, 220),
    "brow": (128, 64, 64),
    "eye_outline": (0, 0, 192),  # 開いている目の輪郭
    "mouth_line": (255, 32, 0),  # 口の線
    "mouth_fill": (128, 0, 0),  # 開いている口の塗りつぶし
    "eye_fill": "white",  # 開いている目の塗りつぶし
}


@dataclass
class FaceConfig:
    """顔の表示設定をまとめたデータクラス."""

    face_words: dict[str, str] = field(default_factory=lambda: FACE_WORDS)
    brow_map: dict[str, int] = field(default_factory=lambda: BROW_MAP)
    eye_map: dict[str, dict[str, float]] = field(
        default_factory=lambda: EYE_MAP
    )
    mouth_map: dict[str, dict[str, float]] = field(
        default_factory=lambda: MOUTH_MAP
    )
    layout_config: dict = field(default_factory=lambda: LAYOUT)
    color_config: dict = field(default_factory=lambda: COLORS)


# ===========================================================================
# ヘルパー関数
# ===========================================================================


def lerp(a: float, b: float, t: float) -> float:
    """線形補間 (Linear Interpolation)."""
    return a + (b - a) * t


# ===========================================================================
# クラス定義
# ===========================================================================


class FaceStrParser:
    def __init__(
        self,
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")

    def parse(self, face_str: str) -> FaceState:
        """parse face string."""
        self.__log.info("face_str=%a", face_str)

        if face_str in FACE_WORDS:
            face_str = FACE_WORDS[face_str]
            self.__log.info(" ==>  face_str=%a", face_str)

        if len(face_str) != 4:
            raise ValueError(
                f"{face_str}: Face string must be 4 characters long"
            )

        brow_char = face_str[0]
        left_eye_char = face_str[1]
        right_eye_char = face_str[2]
        mouth_char = face_str[3]

        face = FaceState()

        # Brow
        if brow_char in BROW_MAP:
            face.brow.tilt = float(BROW_MAP[brow_char])

        # Left Eye
        if left_eye_char in EYE_MAP:
            face.left_eye.open = EYE_MAP[left_eye_char]["open"]
            face.left_eye.curve = EYE_MAP[left_eye_char]["curve"]
            face.left_eye.size = EYE_MAP[left_eye_char]["size"]

        # Right Eye
        if right_eye_char in EYE_MAP:
            face.right_eye.open = EYE_MAP[right_eye_char]["open"]
            face.right_eye.curve = EYE_MAP[right_eye_char]["curve"]
            face.right_eye.size = EYE_MAP[right_eye_char]["size"]

        # Mouth
        if mouth_char in MOUTH_MAP:
            face.mouth.curve = MOUTH_MAP[mouth_char]["curve"]
            face.mouth.open = MOUTH_MAP[mouth_char]["open"]

        return face


class AppMode(ABC):
    """Base class of application mode."""

    FACE_INTERVAL_MIN = 3.0
    FACE_INTERVAL_MAX = 6.0

    GAZE_INTERVAL_MIN = 0.5
    GAZE_INTERVAL_MAX = 2.0

    GAZE_X_MIN = -5.0
    GAZE_X_MAX = +5.0

    def __init__(
        self,
        disp_dev,
        bg_color,
        debug: bool = False,
    ):
        self._debug = debug
        self._log = get_logger(self.__class__.__name__, self._debug)

        self._disp_dev = disp_dev
        self._bg_color = bg_color

        self.face_config = FaceConfig()
        self.parser = FaceStrParser()

        initial_face = self.parser.parse(FACE_WORDS["neutral"])
        self._robot_face = RobotFace(initial_face)

        now = time.time()
        self._next_face_time = now + self.FACE_INTERVAL_MIN
        self._next_gaze_time = now + ANIMATION["gaze_loop_duration"]

    def _new_face(self, now: float, face: str = ""):
        """New face.

        Args:
            now (float): start time in seconds
            face (str): face string.
                "": random
        """
        self._log.info("face=%a", face)

        if not face:
            face = random.choice(list(FACE_WORDS.keys()))
            self._log.info(" random ==> face=%s", face)

        try:
            target_face = self.parser.parse(face)
            self._log.debug("target_face=%s", target_face)
        except Exception as e:
            self._log.error(errmsg(e))
            return

        duration = ANIMATION["face_change_duration"]
        self._robot_face.start_change(target_face, duration=duration)

        self._next_face_time = now + random.uniform(
            self.FACE_INTERVAL_MIN, self.FACE_INTERVAL_MAX
        )

    def _new_gaze(self, now: float) -> None:
        """New gaze."""
        gaze = random.uniform(self.GAZE_X_MIN, self.GAZE_X_MAX)
        self._robot_face.set_gaze(gaze)

        # duration = ANIMATION["gaze_loop_duration"]
        duration = random.uniform(
            self.GAZE_INTERVAL_MIN, self.GAZE_INTERVAL_MAX
        )

        self._log.info("gaze=%.2f, duration=%.2f", gaze, duration)
        self._next_gaze_time = now + duration

    @abstractmethod
    def run(self) -> None:
        """モードのメインループを実行する"""
        pass

    def show_face_outline(self) -> None:
        """Show face outline."""
        self._log.debug("")
        img = self._robot_face.draw_face_outline(
            self._disp_dev.width, self._disp_dev.height, self._bg_color
        )
        self._disp_dev.show_face_outline(img)

    def update_face_and_show(self) -> None:
        self._robot_face.update()

        img = self._robot_face.draw_face_parts(
            self._disp_dev.width, self._disp_dev.height, COLORS["face_bg"]
        )
        self._disp_dev.show_face_parts(img)


class RandomMode(AppMode):
    """ランダムな表情と視線を自動生成して表示するモード。"""

    def __init__(
        self,
        disp_dev,
        bg_color,
        debug: bool = False,
    ):
        """Constractor."""
        super().__init__(
            disp_dev,
            bg_color,
            debug=debug,
        )

        # self._robot_face = RobotFace(
        #     self.parser.parse(FACE_WORDS["neutral"])
        # )

    def run(self) -> None:
        self.show_face_outline()

        interval = ANIMATION["frame_interval"]

        # face outline

        # change face parts
        while True:
            now = time.time()
            if now > self._next_face_time:
                self._new_face(now)

            if now > self._next_gaze_time:
                self._new_gaze(now)

            self.update_face_and_show()

            time.sleep(interval)


class InteractiveMode(AppMode):
    """ユーザーからの入力に基づいて表情を表示するインタラクティブモード。"""

    def __init__(self, disp_dev, bg_color, debug: bool = False):
        super().__init__(disp_dev, bg_color, debug=debug)

    def run(self) -> None:
        """Run."""
        self.show_face_outline()

        self._new_face(time.time(), "_OO_")
        while self._robot_face.is_changing:
            self.update_face_and_show()
            time.sleep(ANIMATION["face_change_duration"])

        while True:
            try:
                user_input = input("顔の記号 (例: _OO_, qで終了): ").strip()
            except EOFError:
                print("\nEOF")
                break

            if user_input.lower() == "q" or not user_input:
                break

            time_start = time.time()
            print(time_start)
            self._new_face(time_start, user_input)
            self._new_gaze(time_start)

            now = time.time()
            while now - time_start < 3.0:
                self.update_face_and_show()
                if now > self._next_gaze_time:
                    self._new_gaze(now)

                time.sleep(ANIMATION["frame_interval"])
                now = time.time()


class FaceUpdater:
    """顔の状態の時間的変化を管理するクラス。"""

    def __init__(
        self,
        face: FaceState,
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("face=%s", face)

        self._change_duration = ANIMATION["face_change_duration"]
        self._change_start_time = 0.0

        self._is_changing = False

        self.start_face = face.copy()
        self.current_face = face.copy()
        self.target_face = face.copy()

        self.current_gaze_x: float = 0.0
        self.target_gaze_x: float = 0.0

    def start_change(
        self, target_face: FaceState, duration: float | None = None
    ) -> None:
        """変形開始."""
        self.__log.debug(
            "duration=%.2f,target_face=%s", duration, target_face
        )

        if not duration:
            duration = ANIMATION["face_change_duration"]
            self.__log.debug(" ==> duration=%s", duration)

        self._chnage_duration = duration  # 表情変化にかかる時間
        self.target_face = target_face.copy()  # ターゲットの表情
        self.start_face = self.current_face.copy()  # 変化前の顔を保存
        self._change_start_time = time.time()  # 変化開始時間
        self._is_changing = True

        self.__log.debug(
            "start_time=%.2f,duration=%.2f",
            self._change_start_time,
            self._change_duration,
        )

    def _update_brow(self, progress_rate):
        self.current_face.brow.tilt = lerp(
            self.start_face.brow.tilt,
            self.target_face.brow.tilt,
            progress_rate,
        )

    def _update_mouth(self, progress_rate):
        self.current_face.mouth.curve = lerp(
            self.start_face.mouth.curve,
            self.target_face.mouth.curve,
            progress_rate,
        )
        self.current_face.mouth.open = lerp(
            self.start_face.mouth.open,
            self.target_face.mouth.open,
            progress_rate,
        )

    def _update_eyes(self, progress_rate):
        cur = self.current_face
        start = self.start_face
        target = self.target_face

        cur.left_eye.open = lerp(
            start.left_eye.open, target.left_eye.open, progress_rate
        )
        cur.left_eye.size = lerp(
            start.left_eye.size, target.left_eye.size, progress_rate
        )
        cur.left_eye.curve = lerp(
            start.left_eye.curve, target.left_eye.curve, progress_rate
        )

        cur.right_eye.open = lerp(
            start.right_eye.open, target.right_eye.open, progress_rate
        )
        cur.right_eye.size = lerp(
            start.right_eye.size, target.right_eye.size, progress_rate
        )
        cur.right_eye.curve = lerp(
            start.right_eye.curve, target.right_eye.curve, progress_rate
        )

    def update(self) -> None:
        # update gaze
        self.current_gaze_x = lerp(
            self.current_gaze_x,
            self.target_gaze_x,
            ANIMATION["gaze_lerp_factor"],
        )
        self.__log.debug(
            "current_gaze_x=%.2f, target_gaze_x=%.2f",
            self.current_gaze_x,
            self.target_gaze_x,
        )

        if not self._is_changing:
            # 表情変化がない場合は、ここでリターン
            return

        #
        # Update Face
        #
        p_rate = self.progress_rate()
        self.__log.debug(
            "elapsed time:%.2f,progress_rate=%.2f",
            self.elapsed_time(),
            p_rate,
        )

        self._update_brow(p_rate)
        self._update_eyes(p_rate)
        self._update_mouth(p_rate)

        if p_rate >= 1.0:
            self._is_changing = False
            self.current_face = self.target_face.copy()
            self.__log.debug("Face change completed: %a", self.current_face)

    def set_gaze(self, x: float) -> None:
        """Set gaze."""
        self.target_gaze_x = x

    @property
    def change_start_time(self):
        """Start time."""
        return self._change_start_time

    @property
    def change_duration(self):
        """Duration."""
        return self._change_duration

    @property
    def change_end_time(self):
        """End time."""
        return self._change_start_time + self._change_duration

    @property
    def is_changing(self) -> bool:
        return self._is_changing

    def elapsed_time(self):
        """Elapsed time."""
        if self._is_changing:
            return time.time() - self.change_start_time

    def progress_rate(self) -> float:
        """Prograss rate."""
        return min(1.0, max(0.0, self.elapsed_time() / self.change_duration))


class DrawFace:
    """顔のパーツを描画するクラス。"""

    def __init__(
        self,
        size: int,  # 正方形一片の長さ
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("size=%s", size)

        self.size = size
        self.scale = size / 100.0

    def _scale_xy(self, x: float, y: float) -> tuple[int, int]:
        return (round(x * self.scale), round(y * self.scale))

    def _scale_width(self, width: float) -> int:
        return round(max(1, int(width * self.scale)))

    def _draw_bezier_curve(self, draw, p0, p1, p2, color, width, steps=5):
        # self.__log.debug(
        #     "p0,p1,p2=%s,%s,%s, color=%s, width=%s", p0, p1, p2, color, width
        # )

        points = []
        for i in range(steps + 1):
            t = i / steps
            bx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
            by = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
            points.append((bx, by))

        draw.line(points, fill=color, width=width, joint="curve")

    def draw_face_outline(
        self,
        screen_width: int,
        screen_height: int,
        bg_color: str | tuple,
    ):
        self.__log.debug(
            "screen: %sx%s, bg_color=%s",
            screen_width,
            screen_height,
            bg_color,
        )
        img = Image.new("RGB", (self.size, self.size), bg_color)
        draw = ImageDraw.Draw(img)

        box = [*self._scale_xy(0, 0), *self._scale_xy(100, 100)]
        draw.rounded_rectangle(
            box,
            radius=20 * self.scale,
            outline=COLORS["line"],
            fill=COLORS["face_bg"],
            width=1,
        )

        final_img = ImageOps.pad(
            img,
            (screen_width, screen_height),
            color=bg_color,
            centering=(0.1, 0.5),  # 位置調整
        )
        return final_img

    def _draw_brows(self, draw, left_cx, right_cx, eye_y, brow_tilt):
        if abs(brow_tilt) <= 1:
            return

        offset_x = LAYOUT["brow_offset_x"]

        brow_y = eye_y + LAYOUT["brow_offset_y"]
        offset_y_factor = LAYOUT["brow_offset_y_factor"]
        offset_y = math.tan(math.radians(brow_tilt)) * offset_y_factor

        color = COLORS["brow"]
        width = self._scale_width(5)

        p1_l = self._scale_xy(left_cx - offset_x, brow_y - offset_y)
        p2_l = self._scale_xy(left_cx + offset_x, brow_y + offset_y)

        draw.line([p1_l, p2_l], fill=color, width=width)

        p1_r = self._scale_xy(right_cx - offset_x, brow_y + offset_y)
        p2_r = self._scale_xy(right_cx + offset_x, brow_y - offset_y)

        draw.line([p1_r, p2_r], fill=color, width=width)

    def _draw_one_eye(
        self,
        draw: ImageDraw.ImageDraw,
        state: list[float],
        pos: list[int],
    ) -> None:
        [eye_size, eye_open, eye_curve] = state
        [eye_x, eye_y, gaze_offset_x] = pos

        eye_w = eye_size * self.scale
        eye_h = eye_w * eye_open
        eye_cx = eye_x + gaze_offset_x

        if eye_h >= ANIMATION["eye_open_threshold"]:
            # 丸い目
            cx, cy = self._scale_xy(eye_cx, eye_y)

            draw.ellipse(
                [cx - eye_w, cy - eye_h, cx + eye_w, cy + eye_h],
                outline=COLORS["eye_outline"],
                fill=COLORS["eye_fill"],
                width=self._scale_width(12),
            )
            return

        # 線の目
        OFFSET_X = LAYOUT["eye_line_offset_x"]
        x1 = eye_cx - OFFSET_X
        x2 = eye_cx + OFFSET_X
        color = COLORS["line"]
        width = self._scale_width(4)

        if eye_curve == 0:
            # 直線
            draw.line(
                [self._scale_xy(x1, eye_y), self._scale_xy(x2, eye_y)],
                fill=color,
                width=width,
            )
            return

        # ベジェ曲線
        OFFSET_Y = LAYOUT["eye_bezier_offset_y"]
        y1 = eye_y + OFFSET_Y * eye_curve / 2
        y2 = eye_y - OFFSET_Y * eye_curve

        p0 = self._scale_xy(x1, y1)
        p2 = self._scale_xy(x2, y1)
        p1 = self._scale_xy(eye_cx, y2)

        self._draw_bezier_curve(draw, p0, p1, p2, color=color, width=width)

    def _draw_eyes(
        self,
        draw,
        face: FaceState,
        gaze_offset_x: float,
    ):
        self.__log.debug("gaze_offset_x=%s", gaze_offset_x)

        eye_y = LAYOUT["eye_y"]
        eye_x1 = LAYOUT["eye_offset"]
        eye_x2 = 100 - eye_x1

        self._draw_one_eye(
            draw,
            [
                face.left_eye.size,
                face.left_eye.open,
                face.left_eye.curve,
            ],
            [eye_x1, eye_y, int(gaze_offset_x)],
        )
        self._draw_one_eye(
            draw,
            [
                face.right_eye.size,
                face.right_eye.open,
                face.right_eye.curve,
            ],
            [
                eye_x2,
                eye_y,
                int(gaze_offset_x),
            ],
        )
        self._draw_brows(
            draw,
            eye_x1,
            eye_x2,
            eye_y,
            face.brow.tilt,
        )

    def _draw_mouth(
        self,
        draw: ImageDraw.ImageDraw,
        face: FaceState,
    ) -> None:
        # self.__log.debug("face=%s", face)

        mouth_cx = 50  # Center
        mouth_cy = LAYOUT["mouth_cy"]

        self.__log.debug("face.mouth=%s", face.mouth)
        open_threshold = ANIMATION["mouth_open_threshold"]

        if face.mouth.open > open_threshold:
            factor = (face.mouth.open - open_threshold) * 2
            r_factor = LAYOUT["mouth_open_radius_factor"]

            r = r_factor * self.scale * factor
            self.__log.debug("r=%s", r)
            if r > 1:
                cx, cy = self._scale_xy(mouth_cx, mouth_cy)
                aspect = ANIMATION["mouth_aspect_ratio"]
                draw.ellipse(
                    [cx - r, cy - r * aspect, cx + r, cy + r * aspect],
                    outline=COLORS["mouth_line"],
                    fill=COLORS["mouth_fill"],
                    width=self._scale_width(4),
                )
                return

        dx = LAYOUT["mouth_curve_half_width"]
        p0 = self._scale_xy(mouth_cx - dx, mouth_cy)
        p2 = self._scale_xy(mouth_cx + dx, mouth_cy)
        p1 = self._scale_xy(mouth_cx, mouth_cy + face.mouth.curve)
        mouth_color = COLORS["mouth_line"]
        mouth_width = self._scale_width(5)

        self._draw_bezier_curve(
            draw, p0, p1, p2, color=mouth_color, width=mouth_width
        )

    def draw_face_parts(
        self,
        face: FaceState,
        gaze_offset_x: float,
        screen_width: int,
        screen_height: int,
        bg_color: str | tuple,
    ):
        self.__log.debug(
            "screen: %sx%s, bg_color=%s",
            screen_width,
            screen_height,
            bg_color,
        )
        img = Image.new("RGB", (self.size, self.size), bg_color)
        draw = ImageDraw.Draw(img)

        # self._draw_outline(draw)
        self._draw_eyes(draw, face, gaze_offset_x)
        self._draw_mouth(draw, face)

        final_img = ImageOps.pad(
            img,
            (screen_width, screen_height),
            color=bg_color,
            centering=(0.1, 0.5),  # 位置調整
        )
        return final_img


class RobotFace:
    """顔の状態管理と描画を統合するファサードクラス。"""

    def __init__(
        self,
        face: FaceState,
        size: int = 240,
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("size=%s", size)

        self.obj_updater = FaceUpdater(
            face=face,
            debug=debug,
        )
        self.obj_draw_face = DrawFace(
            size=size,
            debug=debug,
        )

    @property
    def change_start_time(self):
        """Change start time."""
        return self.obj_updater.change_start_time

    @property
    def change_duration(self):
        """Change duration time."""
        return self.obj_updater.change_duration

    @property
    def elapsed_time(self):
        """get elapsed_time"""
        return self.obj_updater.elapsed_time

    @property
    def is_changing(self) -> bool:
        """flag: is changing."""
        return self.obj_updater.is_changing

    def start_change(
        self,
        state: FaceState,
        duration: float | None = None,
    ) -> None:
        self.obj_updater.start_change(state, duration)

    def set_gaze(self, x: float) -> None:
        self.obj_updater.set_gaze(x)

    def update(self) -> None:
        self.obj_updater.update()

    def draw_face_outline(
        self, screen_width: int, screen_height: int, bg_color: tuple
    ):
        return self.obj_draw_face.draw_face_outline(
            screen_width, screen_height, bg_color
        )

    def draw_face_parts(
        self, screen_width: int, screen_height: int, bg_color: tuple | str
    ):
        return self.obj_draw_face.draw_face_parts(
            self.obj_updater.current_face,
            self.obj_updater.current_gaze_x,
            screen_width,
            screen_height,
            bg_color,
        )


class RobotFaceApp:
    """ロボットの顔のアニメーションアプリケーション。"""

    def __init__(
        self,
        disp_dev: DisplayBase,
        bg_color: str,
        random_mode_enabled: bool = False,
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("bg_color=%s", bg_color)

        self.disp_dev = disp_dev
        self.bg_color = bg_color

        try:
            self.current_mode: AppMode

            if random_mode_enabled:
                self.current_mode = RandomMode(
                    self.disp_dev,
                    self.bg_color,
                    debug=debug,
                )
            else:
                self.current_mode = InteractiveMode(
                    self.disp_dev,
                    self.bg_color,
                    debug=debug,
                )

        except Exception as e:
            self.__log.error(errmsg(e))
            raise

    def end(self) -> None:
        self.disp_dev.close()

    def main(self) -> None:
        self.current_mode.show_face_outline()
        self.current_mode.run()


@click.command("robot_face0.py")
@click.option(
    "-r",
    "--random",
    is_flag=True,
    help="ランダムな表情を自動生成するモードで起動します。",
)
@click.option(
    "--bg-color",
    "--bg",
    type=str,
    default="black",
    show_default=True,
    help="background color",
)
@click.option(
    "--screen-width",
    "-w",
    type=int,
    default=320,
    show_default=True,
    help="Screen Width",
)
@click.option(
    "--screen-height",
    "-h",
    type=int,
    default=240,
    show_default=True,
    help="Screen Height",
)
@click_common_opts(__version__, use_h=False)
def main(ctx, random, bg_color, screen_width, screen_height, debug):
    _log = get_logger(__name__, debug)
    _log.info(
        "random=%s,bg_color=%a,screen=%s",
        random,
        bg_color,
        (screen_width, screen_height),
    )

    app = None
    try:
        disp_dev = get_disp_dev(screen_width, screen_height, debug=debug)

        app = RobotFaceApp(
            disp_dev=disp_dev,
            bg_color=bg_color,
            random_mode_enabled=random,
            debug=debug,
        )

        app.main()

    except KeyboardInterrupt:
        print("\nEnd.")

    except Exception as e:
        _log.error(errmsg(e))

        import traceback

        traceback.print_exc()

    finally:
        if app:
            app.end()


if __name__ == "__main__":
    main()
