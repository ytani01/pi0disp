#
# (c) 2025 Yoichi Tanibayashi
#
"""
ロボットの顔のアニメーション
"""

from __future__ import annotations

import itertools
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


@dataclass
class FaceState:
    """Face status."""

    mouth_curve: float = 0  # 口の曲がり具合: +20(笑顔) ～ -20(への字)
    brow_tilt: float = 0  # 眉毛の角度: +20(下げ) ～ -20(上げ)
    mouth_open: float = 0  # 口の開き具合: 0(線) ～ 1(丸)
    left_eye_openness: float = 1.0
    left_eye_size: float = 8.0
    left_eye_curve: float = 0.0
    right_eye_openness: float = 1.0
    right_eye_size: float = 8.0
    right_eye_curve: float = 0.0

    def copy(self) -> "FaceState":
        """Create a copy of this FaceState."""
        return replace(self)


# ===========================================================================
# 設定セクション
# ===========================================================================

BROW_MAP: dict[str, int] = {"v": 25, "_": 0, "^": -10}
EYE_MAP: dict[str, dict[str, float]] = {
    "O": {"size": 8.0, "openness": 1.0, "curve": 0.0},
    "o": {"size": 6.0, "openness": 1.0, "curve": 0.0},
    "_": {"openness": 0.0, "curve": 0.0},
    "^": {"openness": 0.0, "curve": 1.0},
    "v": {"openness": 0.0, "curve": -1.0},
}
MOUTH_MAP: dict[str, dict[str, float]] = {
    "v": {"curve": 10},
    "_": {"curve": 0},
    "^": {"curve": -10},
    "O": {"open": 1.1},
    "o": {"open": 0.85},
}

MOOD_WORDS = {
    "neutral": "_OO_",
    "zen": "____",
    "happy": "_OOv",
    "smily": "_^^v",
    "sad": "^oo^",
    "angry": "voo^",
    "wink-r": "_O^v",
    "wink-l": "_^Ov",
    "sleepy": "_vv_",
    "surprised": "_ooO",
    "kiss": "_vov",
}

# レイアウト定数 (顔のパーツの相対座標)
LAYOUT = {
    # 眉
    "brow_offset_y": -12,  # 目のY座標からのオフセット
    "brow_offset_x": 9,
    "brow_offset_y_factor": 10,
    # 目
    "eye_y": 45,
    "eye_offset": 30,
    "eye_line_offset_x": 8,
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
    "mouth_aspect_ratio": 1.2,
    "face_change_duration": 0.4,
    "gaze_loop_duration": 3.0,
    "gaze_lerp_factor": 0.4,
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

# ===========================================================================
# ヘルパー関数
# ===========================================================================


@dataclass
class FaceConfig:
    """顔の表示設定をまとめたデータクラス."""

    mood_words: dict[str, str] = field(default_factory=lambda: MOOD_WORDS)
    brow_map: dict[str, int] = field(default_factory=lambda: BROW_MAP)
    eye_map: dict[str, dict[str, float]] = field(
        default_factory=lambda: EYE_MAP
    )
    mouth_map: dict[str, dict[str, float]] = field(
        default_factory=lambda: MOUTH_MAP
    )
    layout_config: dict = field(default_factory=lambda: LAYOUT)
    color_config: dict = field(default_factory=lambda: COLORS)
    animation_config: dict = field(default_factory=lambda: ANIMATION)


def lerp(a: float, b: float, t: float) -> float:
    """線形補間 (Linear Interpolation)."""
    return a + (b - a) * t


# ===========================================================================
# クラス定義
# ===========================================================================


class FaceStateParser:
    def __init__(
        self,
        brow_map: dict[str, int],
        eye_map: dict[str, dict[str, float]],
        mouth_map: dict[str, dict[str, float]],
    ) -> None:
        self._brow_map = brow_map
        self._eye_map = eye_map
        self._mouth_map = mouth_map

    def parse_face_string(self, face_str: str) -> FaceState:
        if len(face_str) != 4:
            raise ValueError(
                f"{face_str}: Face string must be 4 characters long"
            )

        brow_char = face_str[0]
        left_eye_char = face_str[1]
        right_eye_char = face_str[2]
        mouth_char = face_str[3]

        params: dict[str, float] = {}

        # Brow
        if brow_char in self._brow_map:
            params["brow_tilt"] = float(self._brow_map[brow_char])

        # Left Eye
        if left_eye_char in self._eye_map:
            for key, value in self._eye_map[left_eye_char].items():
                params[f"left_eye_{key}"] = value

        # Right Eye
        if right_eye_char in self._eye_map:
            for key, value in self._eye_map[right_eye_char].items():
                params[f"right_eye_{key}"] = value

        # Mouth
        if mouth_char in self._mouth_map:
            if "curve" in self._mouth_map[mouth_char]:
                params["mouth_curve"] = self._mouth_map[mouth_char]["curve"]
                params["mouth_open"] = 0
            if "open" in self._mouth_map[mouth_char]:
                params["mouth_open"] = self._mouth_map[mouth_char]["open"]
                params["mouth_curve"] = 0

        return FaceState(**params)


class FaceMode(ABC):
    """顔のアニメーションモードの抽象基底クラス。"""

    GAZE_X_MIN = -5.0
    GAZE_X_MAX = +5.0

    MOOD_INTERVAL_MIN = 2.0
    MOOD_INTERVAL_MAX = 5.0

    def __init__(
        self,
        disp_dev,
        bg_color,
        robot_face: RobotFace,
        parser: FaceStateParser,
        animation_config: dict,
        debug: bool = False,
    ):
        self._debug = debug
        self._log = get_logger(
            self.__class__.__name__,
            self._debug,
        )

        self._disp_dev = disp_dev
        self._bg_color = bg_color
        self._robot_face = robot_face
        self._parser = parser
        self._animation_config = animation_config

    @abstractmethod
    def run(self) -> None:
        """モードのメインループを実行する"""
        pass

    def update_face_and_show(self) -> None:
        self._robot_face.update()
        img = self._robot_face.draw(
            self._disp_dev.width, self._disp_dev.height, self._bg_color
        )
        self._disp_dev.show(img)


class RandomMode(FaceMode):
    """ランダムな表情と視線を自動生成して表示するモード。"""

    def __init__(
        self,
        disp_dev,
        bg_color,
        robot_face: RobotFace,
        parser: FaceStateParser,
        animation_config: dict,
        mood_words: dict,
        debug: bool = False,
    ):
        super().__init__(
            disp_dev,
            bg_color,
            robot_face,
            parser,
            animation_config,
            debug=debug,
        )
        self.mood_words = mood_words

        now = time.time()

        self._next_mood_time = now + self.MOOD_INTERVAL_MIN

        gaze_duration = self._animation_config["gaze_loop_duration"]
        self._next_gaze_time = now + gaze_duration

    def _handle_random_mood_update(self, now: float):
        if now > self._next_mood_time:
            new_mood_key = random.choice(list(self.mood_words.keys()))
            new_mood = self.mood_words[new_mood_key]
            print(f"{new_mood} {new_mood_key}")

            target_face = self._parser.parse_face_string(new_mood)
            duration = self._animation_config["face_change_duration"]
            assert self._robot_face is not None
            self._robot_face.start_change(target_face, duration=duration)

            self._next_mood_time = now + random.uniform(
                self.MOOD_INTERVAL_MIN, self.MOOD_INTERVAL_MAX
            )

    def _handle_gaze_update(self, now: float) -> None:
        if now > self._next_gaze_time:
            gaze = random.uniform(self.GAZE_X_MIN, self.GAZE_X_MAX)

            self._robot_face.set_gaze(gaze)
            duration = self._animation_config["gaze_loop_duration"]
            self._next_gaze_time = now + duration

    def run(self) -> None:
        interval = self._animation_config["frame_interval"]

        while True:
            now = time.time()
            self._handle_random_mood_update(now)
            self._handle_gaze_update(now)

            self.update_face_and_show()

            time.sleep(interval)


class SequenceMode(FaceMode):
    """定義された表情シーケンスを順に再生するモード。"""

    def __init__(
        self,
        disp_dev,
        bg_color,
        robot_face: RobotFace,
        parser: FaceStateParser,
        animation_config: dict,
        face_str_sequent: list[str],
        debug: bool = False,
    ):
        super().__init__(
            disp_dev,
            bg_color,
            robot_face,
            parser,
            animation_config,
            debug=debug,
        )
        self._face_str_sequent = face_str_sequent

    def run(self) -> None:
        interval = self._animation_config["frame_interval"]

        for face_str in itertools.cycle(self._face_str_sequent):  # 無限
            target_face = self._parser.parse_face_string(face_str)

            duration = self._animation_config["face_change_duration"]
            self._robot_face.start_change(target_face, duration=duration)

            # start_time = self._robot_face.change_start_time
            # while time.time() - start_time < duration:

            while self._robot_face.is_changing:
                self.update_face_and_show()
                time.sleep(interval)

            now = time.time()

            gaze_duration = self._animation_config["gaze_loop_duration"]
            gaze_loop_end_time = now + gaze_duration

            while time.time() < gaze_loop_end_time:
                gaze = random.uniform(self.GAZE_X_MIN, self.GAZE_X_MAX)
                self._robot_face.set_gaze(gaze)

                self.update_face_and_show()

                time.sleep(interval)


class InteractiveMode(FaceMode):
    """ユーザーからの入力に基づいて表情を表示するインタラクティブモード。"""

    def __init__(
        self,
        disp_dev,
        bg_color,
        robot_face: RobotFace,
        parser: FaceStateParser,
        animation_config: dict,
        debug: bool = False,
    ):
        super().__init__(
            disp_dev,
            bg_color,
            robot_face,
            parser,
            animation_config,
            debug=debug,
        )

    def play_interactive_face(self, target_face_str: str) -> None:
        self._log.debug("target_face_str=%s", target_face_str)

        interval = self._animation_config["frame_interval"]

        target_face = self._parser.parse_face_string(target_face_str)

        duration = self._animation_config["face_change_duration"]
        self._robot_face.start_change(target_face, duration=duration)

        # start_time = time.time()
        # while time.time() - start_time < duration:
        while self._robot_face.is_changing:
            self.update_face_and_show()
            time.sleep(interval)

        gaze_duration = self._animation_config["gaze_loop_duration"]
        gaze_loop_end_time = time.time() + gaze_duration
        self._log.debug(
            "Interactive gaze loop started. duration=%s, end_time=%s",
            gaze_duration,
            gaze_loop_end_time,
        )

        while time.time() < gaze_loop_end_time:
            gaze = random.uniform(
                RandomMode.GAZE_X_MIN, RandomMode.GAZE_X_MAX
            )
            assert self._robot_face is not None
            self._robot_face.set_gaze(gaze)
            self.update_face_and_show()
            time.sleep(interval)

    def run(self) -> None:
        while True:
            user_input = input("顔の記号 (例: _OO_, qで終了): ").strip()
            if user_input.lower() == "q" or not user_input:
                break

            try:
                self.play_interactive_face(user_input)
            except ValueError as e:
                print(f"入力エラー: {e}")
            except Exception as e:
                self._log.error(f"予期せぬエラー: {e}")


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
    def show(self, pil_image):
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
            self.lcd = ST7789V(rotation=270, debug=debug)
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

    def show(self, pil_image):
        self.lcd.disp_dev(pil_image)

    def close(self):
        self.lcd.close(True)


class CV2Disp(DisplayBase):
    """OpenCV."""

    def __init__(self, width, height, debug=False):
        super().__init__(width, height, debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("initialized CV2Disp")

    def show(self, pil_image):
        frame = np.array(pil_image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Robot Face", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            raise KeyboardInterrupt("ESC pressed")

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


class FaceAnimator:
    """顔の状態の時間的変化を管理するクラス。"""

    _start_state: FaceState
    _start_time: float
    _duration: float
    _is_changing: bool

    def __init__(
        self,
        initial_state: FaceState,
        animation_config: dict,
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug(
            "initial_state=%s, animation_config=%s",
            initial_state,
            animation_config,
        )

        self._animation_config = animation_config
        self._change_duration = self._animation_config["face_change_duration"]
        self._start_time = time.time()

        self._is_changing = False

        self.current_state = initial_state.copy()
        self.target_face = initial_state.copy()

        self.current_gaze_x: float = 0.0
        self.target_gaze_x: float = 0.0

    def _update_brow(self, t_factor):
        self.current_state.brow_tilt = lerp(
            self._start_state.brow_tilt, self.target_face.brow_tilt, t_factor
        )

    def _update_mouth(self, t_factor):
        self.current_state.mouth_curve = lerp(
            self._start_state.mouth_curve,
            self.target_face.mouth_curve,
            t_factor,
        )
        self.current_state.mouth_open = lerp(
            self._start_state.mouth_open,
            self.target_face.mouth_open,
            t_factor,
        )

    def _update_eyes(self, t_factor):
        cur = self.current_state
        start = self._start_state
        target = self.target_face

        cur.left_eye_openness = lerp(
            start.left_eye_openness, target.left_eye_openness, t_factor
        )
        cur.left_eye_size = lerp(
            start.left_eye_size, target.left_eye_size, t_factor
        )
        cur.left_eye_curve = lerp(
            start.left_eye_curve, target.left_eye_curve, t_factor
        )

        cur.right_eye_openness = lerp(
            start.right_eye_openness, target.right_eye_openness, t_factor
        )
        cur.right_eye_size = lerp(
            start.right_eye_size, target.right_eye_size, t_factor
        )
        cur.right_eye_curve = lerp(
            start.right_eye_curve, target.right_eye_curve, t_factor
        )

    def update(self) -> None:
        self.current_gaze_x = lerp(
            self.current_gaze_x,
            self.target_gaze_x,
            self._animation_config["gaze_lerp_factor"],
        )
        if not self._is_changing:
            return

        self.__log.debug("elapsed time: %f", self.elapsed_time)

        t_factor = min(
            1.0, max(0.0, self.elapsed_time / self._change_duration)
        )

        self._update_brow(t_factor)
        self._update_mouth(t_factor)
        self._update_eyes(t_factor)

        if t_factor >= 1.0:
            self._is_changing = False
            self.current_state = self.target_face.copy()
            self.__log.debug("Face change completed: %a", self.current_state)

    def start_change(
        self,
        target_face: FaceState,
        duration: float | None = None,
    ) -> None:
        """次に変化する顔を指定."""
        self.__log.debug("duration=%s, target_face=%s", duration, target_face)

        if not duration:
            duration = self._animation_config["face_change_duration"]
            self.__log.debug("duration=%s", duration)

        self._chnage_duration = duration
        self.target_face = target_face.copy()

        # 変化前の顔を保存
        self._start_state = self.current_state.copy()

        self._change_start_time = time.time()

        self._is_changing = True

        self.__log.debug(
            "start_time=%s,duration=%s",
            self._change_start_time,
            self._change_duration,
        )

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
    def elapsed_time(self):
        """Elapsed time."""
        if self._is_changing:
            now = time.time()
            return now - self.change_start_time

    @property
    def is_changing(self) -> bool:
        return self._is_changing


class FaceRenderer:
    """顔のパーツを描画するクラス。"""

    def __init__(
        self,
        size: int,
        layout_config: dict,
        color_config: dict,
        animation_config: dict,
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("size=%s", size)

        self.size = size
        self._layout_config = layout_config
        self._color_config = color_config
        self._animation_config = animation_config

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

    def _draw_outline(self, draw):
        box = [*self._scale_xy(0, 0), *self._scale_xy(100, 100)]
        draw.rounded_rectangle(
            box,
            radius=20 * self.scale,
            outline=self._color_config["line"],
            fill=self._color_config["face_bg"],
            width=1,
        )

    def _draw_brows(self, draw, left_cx, right_cx, eye_y, brow_tilt):
        if abs(brow_tilt) <= 1:
            return

        offset_x = self._layout_config["brow_offset_x"]

        brow_y = eye_y + self._layout_config["brow_offset_y"]
        offset_y_factor = self._layout_config["brow_offset_y_factor"]
        offset_y = math.tan(math.radians(brow_tilt)) * offset_y_factor

        color = self._color_config["brow"]
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
        [eye_size, eye_openness, eye_curve] = state
        [eye_x, eye_y, gaze_offset_x] = pos

        eye_w = eye_size * self.scale
        eye_h = eye_w * eye_openness
        eye_cx = eye_x + gaze_offset_x

        if eye_h >= self._animation_config["eye_open_threshold"]:
            # 丸い目
            cx, cy = self._scale_xy(eye_cx, eye_y)

            draw.ellipse(
                [cx - eye_w, cy - eye_h, cx + eye_w, cy + eye_h],
                outline=self._color_config["eye_outline"],
                fill=self._color_config["eye_fill"],
                width=self._scale_width(9),
            )
            return

        # 線の目
        OFFSET_X = self._layout_config["eye_line_offset_x"]
        x1 = eye_cx - OFFSET_X
        x2 = eye_cx + OFFSET_X
        color = self._color_config["line"]
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
        OFFSET_Y = self._layout_config["eye_bezier_offset_y"]
        y1 = eye_y + OFFSET_Y * eye_curve / 2
        y2 = eye_y - OFFSET_Y * eye_curve

        p0 = self._scale_xy(x1, y1)
        p2 = self._scale_xy(x2, y1)
        p1 = self._scale_xy(eye_cx, y2)

        self._draw_bezier_curve(draw, p0, p1, p2, color=color, width=width)

    def _draw_eyes(
        self,
        draw,
        face_state: FaceState,
        gaze_offset_x: float,
    ):
        eye_y = self._layout_config["eye_y"]
        eye_x1 = self._layout_config["eye_offset"]
        eye_x2 = 100 - eye_x1

        self._draw_one_eye(
            draw,
            [
                face_state.left_eye_size,
                face_state.left_eye_openness,
                face_state.left_eye_curve,
            ],
            [eye_x1, eye_y, int(gaze_offset_x)],
        )
        self._draw_one_eye(
            draw,
            [
                face_state.right_eye_size,
                face_state.right_eye_openness,
                face_state.right_eye_curve,
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
            face_state.brow_tilt,
        )

    def _draw_mouth(
        self,
        draw: ImageDraw.ImageDraw,
        face_state: FaceState,
    ) -> None:
        # self.__log.debug("face_state=%s", face_state)

        mouth_cx = 50
        mouth_cy = self._layout_config["mouth_cy"]

        cur_open = face_state.mouth_open
        open_threshold = self._animation_config["mouth_open_threshold"]

        if cur_open > open_threshold:
            factor = (cur_open - open_threshold) * 2
            r_factor = self._layout_config["mouth_open_radius_factor"]

            r = r_factor * self.scale * factor
            self.__log.debug("r=%s", r)
            if r > 1:
                cx, cy = self._scale_xy(mouth_cx, mouth_cy)
                aspect = self._animation_config["mouth_aspect_ratio"]
                draw.ellipse(
                    [cx - r, cy - r * aspect, cx + r, cy + r * aspect],
                    outline=self._color_config["mouth_line"],
                    fill=self._color_config["mouth_fill"],
                    width=self._scale_width(4),
                )
                return

        dx = self._layout_config["mouth_curve_half_width"]
        p0 = self._scale_xy(mouth_cx - dx, mouth_cy)
        p2 = self._scale_xy(mouth_cx + dx, mouth_cy)
        p1 = self._scale_xy(mouth_cx, mouth_cy + face_state.mouth_curve)
        mouth_color = self._color_config["mouth_line"]
        mouth_width = self._scale_width(5)

        self._draw_bezier_curve(
            draw, p0, p1, p2, color=mouth_color, width=mouth_width
        )

    def render(
        self,
        face_state: FaceState,
        gaze_offset_x: float,
        screen_width: int,
        screen_height: int,
        bg_color: str | tuple,
    ):
        img = Image.new("RGB", (self.size, self.size), bg_color)
        draw = ImageDraw.Draw(img)

        self._draw_outline(draw)
        self._draw_eyes(draw, face_state, gaze_offset_x)
        self._draw_mouth(draw, face_state)

        final_img = ImageOps.pad(
            img,
            (screen_width, screen_height),
            color=bg_color,
            centering=(0.1, 0.5),
        )
        return final_img


class RobotFace:
    """顔の状態管理と描画を統合するファサードクラス。"""

    def __init__(
        self,
        initial_state: FaceState,
        size: int = 240,
        layout_config: dict = LAYOUT,
        color_config: dict = COLORS,
        animation_config: dict = ANIMATION,
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("size=%s", size)

        self.animator = FaceAnimator(
            initial_state=initial_state,
            animation_config=animation_config,
            debug=debug,
        )
        self.renderer = FaceRenderer(
            size=size,
            layout_config=layout_config,
            color_config=color_config,
            animation_config=animation_config,
            debug=debug,
        )

    def update(self) -> None:
        self.animator.update()

    def start_change(
        self,
        state: FaceState,
        duration: float | None = None,
    ) -> None:
        self.animator.start_change(state, duration)

    def set_gaze(self, x: float) -> None:
        self.animator.set_gaze(x)

    def draw(self, screen_width: int, screen_height: int, bg_color: tuple):
        return self.renderer.render(
            self.animator.current_state,
            self.animator.current_gaze_x,
            screen_width,
            screen_height,
            bg_color,
        )

    @property
    def change_start_time(self):
        """Change start time."""
        return self.animator.change_start_time

    @property
    def change_duration(self):
        """Change duration time."""
        return self.animator.change_duration

    @property
    def elapsed_time(self):
        """get elapsed_time"""
        return self.animator.elapsed_time

    @property
    def is_changing(self) -> bool:
        """flag: is changing."""
        return self.animator.is_changing


class RobotFaceApp:
    """ロボットの顔のアニメーションアプリケーション。"""

    def __init__(
        self,
        disp_dev: DisplayBase,
        bg_color: str,
        random_mode_enabled: bool = False,
        faces: list[str] | None = None,
        face_config: FaceConfig = FaceConfig(),
        debug: bool = False,
    ) -> None:
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("faces=%s", faces)

        self.disp_dev = disp_dev
        self.bg_color = bg_color
        self.faces = faces

        self.parser = FaceStateParser(
            face_config.brow_map,
            face_config.eye_map,
            face_config.mouth_map,
        )

        try:
            face_size = min(self.disp_dev.width, self.disp_dev.height)
            initial_face_state = self.parser.parse_face_string(
                face_config.mood_words["neutral"]
            )
            self.face = RobotFace(
                initial_state=initial_face_state,
                size=face_size,
                layout_config=face_config.layout_config,
                color_config=face_config.color_config,
                animation_config=face_config.animation_config,
                debug=self.__debug,
            )

            self.current_mode: FaceMode
            if random_mode_enabled:
                self.current_mode = RandomMode(
                    self.disp_dev,
                    self.bg_color,
                    robot_face=self.face,
                    parser=self.parser,
                    animation_config=face_config.animation_config,
                    mood_words=face_config.mood_words,
                    debug=debug,
                )
            elif self.faces:
                self.current_mode = SequenceMode(
                    self.disp_dev,
                    self.bg_color,
                    robot_face=self.face,
                    parser=self.parser,
                    animation_config=face_config.animation_config,
                    face_str_sequent=list(self.faces),
                    debug=debug,
                )
            else:
                self.current_mode = InteractiveMode(
                    self.disp_dev,
                    self.bg_color,
                    robot_face=self.face,
                    parser=self.parser,
                    animation_config=face_config.animation_config,
                    debug=debug,
                )

        except Exception as e:
            self.__log.error(errmsg(e))
            raise

    def end(self) -> None:
        self.disp_dev.close()

    def main(self) -> None:
        self.current_mode.run()


@click.command("robot_face0.py")
@click.argument("faces", nargs=-1)
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
def main(ctx, faces, random, bg_color, screen_width, screen_height, debug):
    _log = get_logger(__name__, debug)
    _log.info(
        "faces=%s,random=%s,bg_color=%a,screen=%s",
        faces,
        random,
        bg_color,
        (screen_width, screen_height),
    )

    faces = list(faces) if faces else None
    app = None
    try:
        disp_dev = get_disp_dev(screen_width, screen_height, debug=debug)

        app = RobotFaceApp(
            disp_dev=disp_dev,
            bg_color=bg_color,
            random_mode_enabled=random,
            faces=faces,
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
