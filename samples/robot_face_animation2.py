#
# (c) 2025 Yoichi Tanibayashi
#
"""
ロボットの顔のアニメーション
"""

import itertools
import math
import random
import socket
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass

import click
from PIL import Image, ImageColor, ImageDraw, ImageOps

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
    brow_tilt: float = 0  # 眉毛の角度(abs(brow_tilt) <= 1: 描画しない)
    mouth_open: float = 0  # 口の開き具合: 0(線) ～ 1(丸)
    left_eye_openness: float = 1.0
    left_eye_size: float = 8.0
    left_eye_curve: float = 0.0
    right_eye_openness: float = 1.0
    right_eye_size: float = 8.0
    right_eye_curve: float = 0.0

    def copy(self):
        return FaceState(
            self.mouth_curve,
            self.brow_tilt,
            self.mouth_open,
            self.left_eye_openness,
            self.left_eye_size,
            self.left_eye_curve,
            self.right_eye_openness,
            self.right_eye_size,
            self.right_eye_curve,
        )


# ===========================================================================
# 設定セクション
# ===========================================================================

MOODS = {
    "neutral": FaceState(),
    "happy": FaceState(mouth_curve=15),
    "sad": FaceState(
        mouth_curve=-10,
        brow_tilt=-10,
        left_eye_size=6,
        right_eye_size=6,
    ),
    "angry": FaceState(
        mouth_curve=-10,
        brow_tilt=25,
        left_eye_size=6,
        right_eye_size=6,
    ),
    "wink-r": FaceState(
        mouth_curve=15,
        left_eye_openness=0.0,
        left_eye_curve=1,
    ),
    "wink-l": FaceState(
        mouth_curve=15,
        right_eye_openness=0.0,
        right_eye_curve=1,
    ),
    "sleepy": FaceState(
        mouth_curve=15,
        left_eye_openness=0.0,
        left_eye_curve=-1,
        right_eye_openness=0.0,
        right_eye_curve=-1,
    ),
    "smily": FaceState(
        mouth_curve=15,
        left_eye_openness=0.0,
        left_eye_curve=1,
        right_eye_openness=0.0,
        right_eye_curve=1,
    ),
    "surprised": FaceState(
        mouth_open=1.1,
        left_eye_size=6,
        right_eye_size=6,
    ),
    "kiss": FaceState(
        mouth_open=0.85,
        left_eye_openness=0.0,
        left_eye_curve=-1,
        right_eye_openness=0.0,
        right_eye_curve=-1,
    ),
}

BROW_MAP: dict[str, int] = {"/": 25, "_": 0, "\\": -10}
EYE_MAP: dict[str, dict[str, float]] = {
    "O": {"size": 8.0, "openness": 1.0, "curve": 0.0},
    "o": {"size": 6.0, "openness": 1.0, "curve": 0.0},
    "-": {"openness": 0.0, "curve": 0.0},
    "^": {"openness": 0.0, "curve": 1.0},
    "v": {"openness": 0.0, "curve": -1.0},
}
MOUTH_MAP: dict[str, dict[str, float]] = {
    "v": {"curve": 15},
    "_": {"curve": 0},
    "^": {"curve": -10},
    "O": {"open": 1.1},
    "o": {"open": 0.85},
}

# レイアウト定数 (顔のパーツの相対座標)
LAYOUT = {
    "eye_y": 45,
    "eye_offset": 30,
    "eye_line_offset_x": 8,
    "eye_bezier_offset_y": 6,
    "mouth_cy": 70,
    "mouth_width": 30,
    "mouth_open_radius_factor": 8,
    "mouth_curve_half_width": 15,
    "brow_y_offset": -12,  # 目のY座標からのオフセット
    "brow_bezier_offset_x": 9,
    "brow_bezier_y_offset_factor": 10,
}

# カラー定数
COLORS = {
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


def lerp(a, b, t):
    """線形補間:ヘルパー関数."""
    return a + (b - a) * t


# ===========================================================================
# クラス定義
# ===========================================================================


class FaceStateParser:
    def parse_face_string(self, face_str: str) -> FaceState:
        if len(face_str) != 4:
            raise ValueError("Face string must be 4 characters long")

        brow_char = face_str[0]
        left_eye_char = face_str[1]
        mouth_char = face_str[2]
        right_eye_char = face_str[3]

        params: dict[str, float] = {}

        # Brow
        if brow_char in BROW_MAP:
            params["brow_tilt"] = float(BROW_MAP[brow_char])

        # Left Eye
        if left_eye_char in EYE_MAP:
            for key, value in EYE_MAP[left_eye_char].items():
                params[f"left_eye_{key}"] = value

        # Right Eye
        if right_eye_char in EYE_MAP:
            for key, value in EYE_MAP[right_eye_char].items():
                params[f"right_eye_{key}"] = value

        # Mouth
        if mouth_char in MOUTH_MAP:
            if "curve" in MOUTH_MAP[mouth_char]:
                params["mouth_curve"] = MOUTH_MAP[mouth_char]["curve"]
                params["mouth_open"] = 0
            if "open" in MOUTH_MAP[mouth_char]:
                params["mouth_open"] = MOUTH_MAP[mouth_char]["open"]
                params["mouth_curve"] = 0

        return FaceState(**params)


class DisplayOutput(ABC):
    """ディスプレイ出力を抽象化するクラス"""

    def __init__(self, debug=False):
        """Constructor."""
        self.__debug = debug
        self.__log = get_logger(DisplayOutput.__name__, self.__debug)
        self.__log.debug("(abstract)")

    @abstractmethod
    def show(self, pil_image):
        """画像をデバイスに転送"""
        pass

    @abstractmethod
    def close(self):
        """リソース解放"""
        pass


class LcdOutput(DisplayOutput):
    """LCD Output (ST7789V)."""

    def __init__(self, debug=False):
        super().__init__(debug=debug)
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

        self.__log.debug("Found LCD, returning LcdOutput.")

    def _check_pigpio(self, host="localhost", port=8888, timeout=0.1):
        """pigpioデーモンの存在確認"""
        try:
            with socket.create_connection((host, port), timeout=timeout):
                return True
        except OSError:
            return False

    def show(self, pil_image):
        self.lcd.display(pil_image)

    def close(self):
        self.lcd.close(True)


class PreviewOutput(DisplayOutput):
    """OpenCV."""

    def __init__(self, debug=False):
        super().__init__(debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("initialized PreviewOutput")

    def show(self, pil_image):
        # PIL -> OpenCV (BGR)
        frame = np.array(pil_image)
        frame = cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)
        cv2.imshow("Robot Face", frame)
        key = cv2.waitKey(1) & 0xFF
        if key == 27:  # ESC
            raise KeyboardInterrupt("ESC pressed")

    def close(self):
        cv2.destroyAllWindows()


def create_output_device(debug=False) -> DisplayOutput:
    """利用可能な出力デバイスを検出して返すファクトリ関数"""
    _log = get_logger("()", debug)

    # 1. ハードウェア (ST7789) の確認
    if HAS_LCD:
        try:
            return LcdOutput(debug=debug)
        except Exception as e:
            _log.error(errmsg(e))

    # 2. OpenCVプレビュー
    if HAS_OPENCV:
        _log.warning("Found OpenCV, returning PreviewOutput.")
        return PreviewOutput(debug=debug)

    # 3. なし
    _log.warning("警告: 表示可能なデバイスがありません (コンソール実行のみ)")
    # 実際には、何も表示しないDummyOutputなどを返すことも検討できる
    raise RuntimeError("No suitable display output device found.")


class RobotFace:
    """顔の状態管理と描画を担当するクラス"""

    _start_state: FaceState  # 追加
    _change_start_time: float  # 追加
    _change_duration: float  # 追加
    _is_changing: bool  # 追加

    def __init__(
        self,
        initial_state: FaceState,
        size=240,
        debug=False,
        change_duration: float = 0.5,
    ):
        """Constructor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("initial_state=%a,size=%s", initial_state, size)

        self._change_duration = change_duration
        self._is_changing = False
        self._change_start_time: float = time.time()  # 初期化を追加

        self.size = size

        self.current_state = initial_state.copy()
        self.target_state = initial_state.copy()

        # 描画用ヘルパー係数
        self.scale = size / 100.0

        # 視線状態管理
        self.current_gaze_x: float = 0.0
        self.target_gaze_x: float = 0.0

    def update(self):
        """状態をターゲットに近づける"""
        # 視線は常に更新する
        self.current_gaze_x = lerp(
            self.current_gaze_x, self.target_gaze_x, 0.8
        )
        self.__log.debug(
            "Face gaze updated. current_gaze_x=%s, target_gaze_x=%s",
            self.current_gaze_x,
            self.target_gaze_x,
        )

        if not self._is_changing:
            return

        now = time.time()
        elapsed_time = now - self._change_start_time
        t_factor = min(1.0, max(0.0, elapsed_time / self._change_duration))

        c, t = self.current_state, self.target_state
        s = self._start_state

        c.mouth_curve = lerp(s.mouth_curve, t.mouth_curve, t_factor)
        c.brow_tilt = lerp(s.brow_tilt, t.brow_tilt, t_factor)
        c.mouth_open = lerp(s.mouth_open, t.mouth_open, t_factor)

        # left eye
        c.left_eye_openness = lerp(
            s.left_eye_openness, t.left_eye_openness, t_factor
        )
        c.left_eye_size = lerp(s.left_eye_size, t.left_eye_size, t_factor)
        c.left_eye_curve = lerp(s.left_eye_curve, t.left_eye_curve, t_factor)

        # right eye
        c.right_eye_openness = lerp(
            s.right_eye_openness, t.right_eye_openness, t_factor
        )
        c.right_eye_size = lerp(s.right_eye_size, t.right_eye_size, t_factor)
        c.right_eye_curve = lerp(
            s.right_eye_curve, t.right_eye_curve, t_factor
        )

        if t_factor >= 1.0:
            self._is_changing = False
            self.current_state = self.target_state.copy()
            self.__log.debug(
                "Face change completed. current_state=%a", self.current_state
            )

    def set_target_state(
        self, state: FaceState, duration: float | None = None
    ):
        """状態セット"""
        self._start_state = self.current_state.copy()  # 追加
        self._change_start_time = time.time()  # 追加
        self.target_state = state.copy()
        self._change_duration = (
            duration if duration is not None else self._change_duration
        )  # 修正
        self._is_changing = True  # 追加
        self.__log.debug(
            "Target state set. target_state=%a, duration=%s",
            self.target_state,
            self._change_duration,
        )

    def set_gaze(self, x):
        """視線セット (-20 to +20)"""
        self.target_gaze_x = x

    def _xy(self, x, y):
        return (round(x * self.scale), round(y * self.scale))

    def _w(self, width) -> int:
        return round(max(1, int(width * self.scale)))

    def _draw_bezier_curve(self, draw, p0, p1, p2, color, width, steps=5):
        """3点の制御点からベジェ曲線を計算して描画する"""
        self.__log.debug(
            "p0,p1,p2=%s,%s,%s, color=%s, width=%s", p0, p1, p2, color, width
        )

        points = []
        for i in range(steps + 1):
            t = i / steps
            # 2次ベジェ曲線の公式
            bx = (1 - t) ** 2 * p0[0] + 2 * (1 - t) * t * p1[0] + t**2 * p2[0]
            by = (1 - t) ** 2 * p0[1] + 2 * (1 - t) * t * p1[1] + t**2 * p2[1]
            points.append((bx, by))

        draw.line(points, fill=color, width=width, joint="curve")

    def _draw_outline(self, draw):
        box = [*self._xy(0, 0), *self._xy(100, 100)]
        draw.rounded_rectangle(
            box,
            radius=20 * self.scale,
            outline=COLORS["line"],
            fill=COLORS["face_bg"],
            width=1,
        )

    def _draw_one_eye(
        self,
        draw,
        eye_x,
        eye_y,
        eye_size,
        eye_openness,
        eye_curve,
        gaze_offset,
    ):
        """Drow one eye."""
        eye_cx = eye_x + gaze_offset  # 視線を加味した中心X
        self.__log.debug("Drawing eye with gaze_offset=%s", gaze_offset)

        eye_w = eye_size * self.scale  # 目のサイズ(幅)
        eye_h = eye_w * eye_openness  # 開き具合をかけた目の高さ

        # 描画
        if eye_h >= 6:
            #
            # 開いている場合: 楕円
            #
            cx, cy = self._xy(eye_cx, eye_y)
            draw.ellipse(
                [cx - eye_w, cy - eye_h, cx + eye_w, cy + eye_h],
                outline=COLORS["eye_outline"],
                fill=COLORS["eye_fill"],
                width=self._w(9),
            )
            return

        #
        # eye_h < 6: 目が閉じている場合
        #
        LINE_OFFSET_X = LAYOUT["eye_line_offset_x"]
        x1 = eye_cx - LINE_OFFSET_X
        x2 = eye_cx + LINE_OFFSET_X

        if eye_curve == 0:
            #
            # 直線
            #
            draw.line(
                [self._xy(x1, eye_y), self._xy(x2, eye_y)],
                fill=COLORS["line"],
                width=self._w(4),
            )
            return

        #
        # eye_curve != 0: ベジェ曲線
        #
        BEZIER_OFFSET_Y = LAYOUT["eye_bezier_offset_y"]
        y1 = eye_y + BEZIER_OFFSET_Y * eye_curve / 2
        y2 = eye_y - BEZIER_OFFSET_Y * eye_curve

        p0 = self._xy(x1, y1)
        p2 = self._xy(x2, y1)
        p1 = self._xy(eye_cx, y2)

        self._draw_bezier_curve(
            draw, p0, p1, p2, color=COLORS["line"], width=self._w(4)
        )

    def _draw_brows(self, draw, left_cx, right_cx, eye_y, brow_tilt):
        """Draw brows."""
        if abs(brow_tilt) <= 1:
            # 描画しない
            return

        brow_y = eye_y + LAYOUT["brow_y_offset"]
        offset_y = (
            math.tan(math.radians(brow_tilt))
            * LAYOUT["brow_bezier_y_offset_factor"]
        )

        # 左眉
        p1_l = self._xy(
            left_cx - LAYOUT["brow_bezier_offset_x"],
            brow_y - offset_y,
        )
        p2_l = self._xy(
            left_cx + LAYOUT["brow_bezier_offset_x"],
            brow_y + offset_y,
        )
        draw.line([p1_l, p2_l], fill=COLORS["brow"], width=self._w(5))

        # 右眉
        # 右目の眉毛はX軸方向のオフセットの符号が逆になる
        p1_r = self._xy(
            right_cx - LAYOUT["brow_bezier_offset_x"],
            brow_y + offset_y,
        )
        p2_r = self._xy(
            right_cx + LAYOUT["brow_bezier_offset_x"],
            brow_y - offset_y,
        )
        draw.line([p1_r, p2_r], fill=COLORS["brow"], width=self._w(5))

    def _draw_eyes(self, draw):
        """Draw both eyes and brows."""
        eye_y = LAYOUT["eye_y"]
        eye_offset = LAYOUT["eye_offset"]
        cs = self.current_state

        self._draw_one_eye(
            draw,
            eye_offset,
            eye_y,
            cs.left_eye_size,
            cs.left_eye_openness,
            cs.left_eye_curve,
            self.current_gaze_x,
        )
        self._draw_one_eye(
            draw,
            100 - eye_offset,
            eye_y,
            cs.right_eye_size,
            cs.right_eye_openness,
            cs.right_eye_curve,
            self.current_gaze_x,
        )
        self._draw_brows(
            draw,
            eye_offset,  # left_brow_cx (視線に追従しない)
            100 - eye_offset,  # right_brow_cx (視線に追従しない)
            eye_y,
            self.current_state.brow_tilt,
        )

    def _draw_mouth(self, draw):
        """Draw mouth."""
        mouth_cx = 50  # 水平中央
        mouth_cy = LAYOUT["mouth_cy"]
        st = self.current_state

        if st.mouth_open > 0.5:
            # 丸い口 (驚きなど)
            factor = (st.mouth_open - 0.5) * 2
            r = LAYOUT["mouth_open_radius_factor"] * self.scale * factor
            if r > 1:
                cx, cy = self._xy(mouth_cx, mouth_cy)
                draw.ellipse(
                    [cx - r, cy - r * 1.2, cx + r, cy + r * 1.2],
                    outline=COLORS["mouth_line"],
                    fill=COLORS["mouth_fill"],
                    width=self._w(4),
                )
            return

        # カーブする口
        dx = LAYOUT["mouth_curve_half_width"]
        p0 = self._xy(mouth_cx - dx, mouth_cy)
        p2 = self._xy(mouth_cx + dx, mouth_cy)
        p1 = self._xy(mouth_cx, mouth_cy + st.mouth_curve)
        c0 = COLORS["mouth_line"]
        w0 = self._w(5)

        self._draw_bezier_curve(draw, p0, p1, p2, color=c0, width=w0)

    def draw(self, screen_width: int, screen_height: int, bg_color: tuple):
        # 画像生成
        # 正方形キャンバスを作成してからパディングする
        img = Image.new("RGB", (self.size, self.size), bg_color)
        draw = ImageDraw.Draw(img)

        self._draw_outline(draw)
        self._draw_eyes(draw)
        self._draw_mouth(draw)

        # パディングして画面サイズに合わせる (中央寄せなど)
        final_img = ImageOps.pad(
            img,
            (screen_width, screen_height),
            color=bg_color,
            centering=(0.1, 0.5),
        )
        return final_img

    @property
    def is_changing(self) -> bool:
        """Is face changing?"""
        return self._is_changing


class RobotFaceApp:
    """Robot face App class."""

    def __init__(
        self,
        output: DisplayOutput,
        screen_width: int,
        screen_height: int,
        bg_color: str,
        all_moods: dict[str, FaceState],  # 追加
        face_change_duration: float = 0.5,  # 追加
        init_mood: str = "neutral",
        face_sequence: list[FaceState] | None = None,
        debug=False,
    ):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug(
            "init_mood=%a, face_sequence=%s", init_mood, face_sequence
        )

        self.output = output
        self.screen_width = screen_width
        self.screen_height = screen_height
        self.bg_color = bg_color
        self.bg_color_tuple = ImageColor.getrgb(bg_color)
        self.all_moods = all_moods  # 追加
        self.face_change_duration = face_change_duration  # 追加
        self.init_mood = init_mood
        self.face_sequence = face_sequence

        # アニメーションタイミング管理
        now = time.time()
        self._next_mood_time: float = now + 5.0
        self._next_gaze_time: float = now + 5.0

        # 視線制御用の状態変数
        self._gaze_interval_min: float = 0.5
        self._gaze_interval_max: float = 2.0
        self._gaze_width_range_min: float = -15.0
        self._gaze_width_range_max: float = 15.0

        try:
            face_size = min(self.screen_width, self.screen_height)
            self.face = RobotFace(
                all_moods[self.init_mood],
                size=face_size,
                debug=self.__debug,  # 変更
                change_duration=self.face_change_duration,
            )
        except Exception as e:
            self.__log.error(errmsg(e))
            raise e

    def _handle_random_mood_update(self, now: float):
        # 表情変更
        if now > self._next_mood_time:
            new_mood = random.choice(list(self.all_moods.keys()))
            print(f"mood: {new_mood}")
            self.face.set_target_state(
                self.all_moods[new_mood], duration=random.uniform(0.5, 1.5)
            )
            self._next_mood_time = now + random.uniform(3.0, 5.0)

    def _handle_gaze_update(self, now: float):
        # 視線変更
        if now > self._next_gaze_time:
            gaze = random.uniform(
                self._gaze_width_range_min, self._gaze_width_range_max
            )
            self.face.set_gaze(gaze)
            self._next_gaze_time = now + random.uniform(
                self._gaze_interval_min, self._gaze_interval_max
            )
            self.__log.debug(
                "Gaze target changed to %s. Current gaze_x=%s",
                gaze,
                self.face.current_gaze_x,
            )

    def main(self):
        """Main."""
        if self.face_sequence:
            # シーケンス再生モード
            for state in itertools.cycle(self.face_sequence):
                self.play_interactive_face(state)
            return

        # ランダム再生モード
        if not self.init_mood:
            self.init_mood = "neutral"
            self.__log.info("mood=%a", self.init_mood)

        while True:
            now = time.time()

            self._handle_random_mood_update(now)  # ヘルパーメソッド呼び出し
            self._handle_gaze_update(now)  # ヘルパーメソッド呼び出し

            # 更新と描画
            self.face.update()
            img = self.face.draw(
                self.screen_width,
                self.screen_height,
                self.bg_color_tuple,
            )
            self.output.show(img)

            time.sleep(0.1)

    def end(self):
        """End."""
        self.output.close()

    def play_interactive_face(self, target_state: FaceState):
        """インタラクティブモードで単一の表情を表示し、目のキョロキョロ動作を行う."""
        # 1. 表情を設定・変化させる
        self.face.set_target_state(target_state, duration=0.25)
        start_time = time.time()
        while time.time() - start_time < 0.25:
            self.face.update()
            img = self.face.draw(
                self.screen_width,
                self.screen_height,
                self.bg_color_tuple,
            )
            self.output.show(img)
            time.sleep(0.05)

        # 表情変化後、キョロキョロ動作を一定時間行う
        gaze_loop_duration = 4.75
        gaze_loop_end_time = time.time() + gaze_loop_duration
        self.__log.debug(
            "Interactive gaze loop started. duration=%s, end_time=%s",
            gaze_loop_duration,
            gaze_loop_end_time,
        )

        # gaze_loop_end_timeまでキョロキョロ動作を続ける
        while time.time() < gaze_loop_end_time:
            now = time.time()
            self._handle_gaze_update(now)  # 共通の視線更新ロジックを使用
            self.face.update()
            img = self.face.draw(
                self.screen_width,
                self.screen_height,
                self.bg_color_tuple,
            )
            self.output.show(img)
            time.sleep(0.05)


@click.command(__file__.split("/")[-1])  # file name
@click.argument("faces", nargs=-1)
@click.option(
    "-r",
    "--random",
    is_flag=True,
    help="ランダムな表情を自動生成するモードで起動します。",
)
@click_common_opts(__version__)
def main(ctx, faces, random, debug):
    """Main."""
    __log = get_logger(__name__, debug)
    __log.info("faces=%s, random=%s", faces, random)

    app = None
    try:
        output_device = create_output_device(debug=debug)
        parser = FaceStateParser()  # ここでインスタンスを作成

        app = RobotFaceApp(
            output_device,
            320,  # SCREEN_WIDTH
            240,  # SCREEN_HEIGHT
            "black",  # BG_COLOR
            all_moods=MOODS,  # MOODS 辞書を渡す
            face_change_duration=2.0,  # 追加
            init_mood="neutral",  # デフォルト mood を設定
            debug=debug,
        )

        if random:
            # ランダム再生モード
            app.main()
        elif faces:
            # コマンドライン引数がある場合: シーケンス再生モード
            app.face_sequence = [parser.parse_face_string(f) for f in faces]
            app.main()
        else:
            # コマンドライン引数がない場合: インタラクティブモード
            while True:
                user_input = input("顔の記号 (例: _O_O, qで終了): ").strip()
                if user_input.lower() == "q" or not user_input:
                    break  # 終了

                try:
                    target_face_state = parser.parse_face_string(user_input)
                    app.play_interactive_face(target_face_state)

                except ValueError as e:
                    __log.error(f"入力エラー: {e}")
                except Exception as e:
                    __log.error(errmsg(e))
    except KeyboardInterrupt:
        print("\nEnd.")
    except Exception as e:
        __log.error(errmsg(e))
    finally:
        if app:
            app.end()


if __name__ == "__main__":
    main()
