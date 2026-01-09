#
# (c) 2025 Yoichi Tanibayashi
#
"""
ST7789Vディスプレイで動作する、物理ベースのアニメーションデモ。
見た目維持・計算処理最適化版。
"""

import colorsys
import math
import os
import time
from typing import List, Optional

import click
import numpy as np
import psutil
from PIL import Image, ImageDraw, ImageFont

from .. import (
    __version__,
    click_common_opts,
    draw_text,
    get_ip_address,
    get_logger,
)
from ..disp.disp_spi import SpiPins
from ..disp.st7789v import ST7789V
from ..utils.utils import expand_bbox, merge_bboxes

__log = get_logger(__name__)

# --- 元の見た目設定を維持 ---
SPI_SPEED_HZ = 8_000_000
TARGET_FPS = 30.0
BALL_RADIUS = 20
FONT_PATH = "Firge-Regular.ttf"
TEXT_COLOR = (255, 255, 255)
FPS_UPDATE_INTERVAL = 0.2

# --- 計算最適化のみの設定 ---
PHYSICS_SUBSTEPS = 4  # 物理精度維持
COLLISION_CHECK_SKIP = 2  # 衝突チェックのみ軽量化
MAX_SPEED_SQ = 1000000.0  # speed^2での比較用（1000^2）

# 事前計算済み定数
TWO_PI = 2.0 * math.pi
SQRT_CACHE: dict[float, float] = {}  # 平方根キャッシュ
COS_SIN_CACHE: dict[float, tuple[float, float]] = {}  # 三角関数キャッシュ


# --- 高速化ヘルパー関数 ---
def fast_sqrt(value):
    """キャッシュ付き高速平方根計算"""
    if value in SQRT_CACHE:
        return SQRT_CACHE[value]
    result = math.sqrt(value)
    if len(SQRT_CACHE) < 1000:  # キャッシュサイズ制限
        SQRT_CACHE[value] = result
    return result


def fast_cos_sin(angle):
    """キャッシュ付き三角関数計算"""
    # 角度を適度に量子化してキャッシュヒット率向上
    quantized = round(angle * 100) / 100
    if quantized in COS_SIN_CACHE:
        return COS_SIN_CACHE[quantized]

    cos_val = math.cos(quantized)
    sin_val = math.sin(quantized)
    if len(COS_SIN_CACHE) < 500:
        COS_SIN_CACHE[quantized] = (cos_val, sin_val)
    return cos_val, sin_val


# --- 最適化されたクラス定義 ---
class Ball:
    """計算最適化版ボールクラス（見た目は同じ）"""

    __slots__ = (
        "x",
        "y",
        "radius",
        "speed_x",
        "speed_y",
        "fill_color",
        "prev_bbox",
        "speed_sq",
        "_bbox_cache",
        "_bbox_dirty",
    )

    def __init__(self, x, y, radius, speed, angle, fill_color):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius

        # 三角関数計算を事前実行
        cos_a, sin_a = fast_cos_sin(angle)
        self.speed_x = speed * cos_a
        self.speed_y = speed * sin_a
        self.speed_sq = speed * speed  # 速度の二乗を事前計算

        self.fill_color = fill_color
        self.prev_bbox: Optional[tuple[int, int, int, int]] = None
        self._bbox_cache = None
        self._bbox_dirty = True

    def update_position(self, delta_t, screen_width, screen_height):
        """位置更新（計算最適化版）"""
        # インライン計算で関数呼び出しオーバーヘッド削減
        new_x = self.x + self.speed_x * delta_t
        new_y = self.y + self.speed_y * delta_t

        # 境界チェック（分岐予測最適化）
        r = self.radius
        width_limit = screen_width - r
        height_limit = screen_height - r

        # X軸境界チェック
        if new_x <= r:
            new_x = r
            self.speed_x = -self.speed_x
        elif new_x >= width_limit:
            new_x = width_limit - 1
            self.speed_x = -self.speed_x

        # Y軸境界チェック
        if new_y <= r:
            new_y = r
            self.speed_y = -self.speed_y
        elif new_y >= height_limit:
            new_y = height_limit - 1
            self.speed_y = -self.speed_y

        # 位置更新時に速度の二乗も更新
        self.speed_sq = (
            self.speed_x * self.speed_x + self.speed_y * self.speed_y
        )

        # 位置が変わったらbboxキャッシュを無効化
        if new_x != self.x or new_y != self.y:
            self.x = new_x
            self.y = new_y
            self._bbox_dirty = True

    def get_bbox(self):
        """バウンディングボックス取得（キャッシュ付き）"""
        if self._bbox_dirty or self._bbox_cache is None:
            r = self.radius
            x_int = int(self.x)
            y_int = int(self.y)
            self._bbox_cache = (x_int - r, y_int - r, x_int + r, y_int + r)
            self._bbox_dirty = False
        return self._bbox_cache

    def draw(self, draw: ImageDraw.ImageDraw):
        """描画処理（変更なし）"""
        bbox = self.get_bbox()
        draw.ellipse(bbox, fill=self.fill_color, outline=self.fill_color)


class FpsCounter:
    """FPSカウンター（計算最適化版）"""

    __slots__ = (
        "frame_count",
        "last_update_time",
        "fps_text",
        "_update_threshold",
    )

    def __init__(self):
        self.frame_count = 0
        self.last_update_time = time.time()
        self.fps_text = "FPS: --"
        self._update_threshold = FPS_UPDATE_INTERVAL  # 閾値を事前計算

    def update(self) -> bool:
        """FPS更新（除算最小化）"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_update_time

        if elapsed >= self._update_threshold:
            # 除算を1回のみ実行
            fps = self.frame_count / elapsed
            self.fps_text = f"FPS: {fps:.0f}"
            self.frame_count = 0
            self.last_update_time = current_time
            return True
        return False


class BenchmarkTracker:
    """ベンチマーク計測クラス"""

    def __init__(self, duration: float = 10.0):
        self.duration = duration
        self.start_time: Optional[float] = None
        self.total_frames = 0
        self.process = psutil.Process(os.getpid())
        self.pigpiod_process: Optional[psutil.Process] = None
        self.cpu_samples: List[float] = []
        self.pigpiod_samples: List[float] = []

        # pigpiod プロセスを特定
        for p in psutil.process_iter(["name"]):
            try:
                if p.info["name"] == "pigpiod":
                    self.pigpiod_process = p
                    break
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

    def start(self):
        self.start_time = time.time()
        # 初回のCPU負荷計測（基準値）
        self.process.cpu_percent(interval=None)
        if self.pigpiod_process:
            self.pigpiod_process.cpu_percent(interval=None)

    def update(self):
        if self.start_time is None:
            return

        self.total_frames += 1

        # 1秒ごとにCPU負荷をサンプリング
        elapsed = time.time() - self.start_time
        if int(elapsed) > len(self.cpu_samples):
            self.cpu_samples.append(self.process.cpu_percent(interval=None))
            if self.pigpiod_process:
                self.pigpiod_samples.append(
                    self.pigpiod_process.cpu_percent(interval=None)
                )

    def should_stop(self) -> bool:
        if self.start_time is None:
            return False
        return (time.time() - self.start_time) >= self.duration

    def get_results(self) -> dict:
        elapsed = time.time() - (self.start_time or time.time())
        avg_fps = self.total_frames / elapsed if elapsed > 0 else 0
        avg_cpu = (
            sum(self.cpu_samples) / len(self.cpu_samples)
            if self.cpu_samples
            else 0
        )
        avg_pigpiod = (
            sum(self.pigpiod_samples) / len(self.pigpiod_samples)
            if self.pigpiod_samples
            else 0
        )

        return {
            "duration": elapsed,
            "avg_fps": avg_fps,
            "avg_cpu": avg_cpu,
            "avg_pigpiod": avg_pigpiod,
            "total_frames": self.total_frames,
        }


# --- 計算最適化されたヘルパー関数 ---
def _initialize_balls_optimized(
    num_balls: int, width: int, height: int, ball_speed: float
) -> List[Ball]:
    """ボール初期化（計算最適化版）"""
    balls: List[Ball] = []
    speed = ball_speed if ball_speed is not None else 300.0
    max_attempts_per_ball = 100

    # 色相計算を事前実行
    hue_values = [i / num_balls for i in range(num_balls)]
    np.random.shuffle(hue_values)

    # 配置範囲を事前計算
    min_pos = BALL_RADIUS
    max_x = width - BALL_RADIUS
    max_y = height - BALL_RADIUS

    for i in range(num_balls):
        ball_placed = False
        hue = hue_values[i]

        # RGB色を事前計算
        rgb_float = colorsys.hsv_to_rgb(hue, 1.0, 1.0)
        fill_color = tuple(int(c * 255) for c in rgb_float)

        for _ in range(max_attempts_per_ball):
            x = np.random.randint(min_pos, max_x)
            y = np.random.randint(min_pos, max_y)

            # 重なりチェック（距離の二乗で比較して平方根計算を回避）
            min_dist_sq = (BALL_RADIUS * 2) ** 2
            is_valid = True

            for existing_ball in balls:
                dx = x - existing_ball.x
                dy = y - existing_ball.y
                dist_sq = dx * dx + dy * dy

                if dist_sq <= min_dist_sq:
                    is_valid = False
                    break

            if is_valid:
                angle = np.random.rand() * TWO_PI
                balls.append(
                    Ball(x, y, BALL_RADIUS, speed, angle, fill_color)
                )
                ball_placed = True
                break

        if not ball_placed:
            __log.warning(f"ボール{len(balls) + 1}を配置できませんでした。")

    return balls


def _handle_ball_collisions_optimized(balls: List[Ball], frame_count: int):
    """衝突処理（計算最適化版）"""
    # フレームスキップで計算負荷削減（見た目への影響は最小）
    if frame_count % COLLISION_CHECK_SKIP != 0:
        return

    num_balls = len(balls)
    radii_sum = BALL_RADIUS * 2  # 全ボール同サイズなので事前計算
    radii_sum_sq = radii_sum * radii_sum
    min_dist_sq = (radii_sum * 0.05) ** 2

    for i in range(num_balls):
        ball1 = balls[i]
        for j in range(i + 1, num_balls):
            ball2 = balls[j]

            # 距離計算（平方根回避）
            dx = ball1.x - ball2.x
            dy = ball1.y - ball2.y
            dist_sq = dx * dx + dy * dy

            # 早期リターン（衝突していない）
            if dist_sq >= radii_sum_sq:
                continue

            # 極近距離処理
            if dist_sq <= min_dist_sq:
                # ランダム分離（三角関数キャッシュ使用）
                angle = np.random.rand() * TWO_PI
                cos_a, sin_a = fast_cos_sin(angle)
                sep_dist = radii_sum * 0.55

                sep_x = cos_a * sep_dist * 0.5
                sep_y = sin_a * sep_dist * 0.5

                ball1.x += sep_x
                ball1.y += sep_y
                ball2.x -= sep_x
                ball2.y -= sep_y

                ball1._bbox_dirty = True
                ball2._bbox_dirty = True
                continue

            # 通常の衝突処理
            # 平方根計算を1回のみ実行
            dist = fast_sqrt(dist_sq)
            inv_dist = 1.0 / dist  # 除算を1回のみ
            nx = dx * inv_dist
            ny = dy * inv_dist

            # 相対速度計算
            rel_vx = ball1.speed_x - ball2.speed_x
            rel_vy = ball1.speed_y - ball2.speed_y
            rel_v_normal = rel_vx * nx + rel_vy * ny

            # 接近している場合のみ処理
            if rel_v_normal < 0:
                # 接線ベクトル
                tx = -ny
                ty = nx

                # 速度成分分解
                v1n = ball1.speed_x * nx + ball1.speed_y * ny
                v1t = ball1.speed_x * tx + ball1.speed_y * ty
                v2n = ball2.speed_x * nx + ball2.speed_y * ny
                v2t = ball2.speed_x * tx + ball2.speed_y * ty

                # 速度交換
                new_v1x = v2n * nx + v1t * tx
                new_v1y = v2n * ny + v1t * ty
                new_v2x = v1n * nx + v2t * tx
                new_v2y = v1n * ny + v2t * ty

                # 速度上限チェック（二乗比較で高速化）
                if (
                    new_v1x * new_v1x + new_v1y * new_v1y <= MAX_SPEED_SQ
                    and new_v2x * new_v2x + new_v2y * new_v2y <= MAX_SPEED_SQ
                ):
                    ball1.speed_x = new_v1x
                    ball1.speed_y = new_v1y
                    ball2.speed_x = new_v2x
                    ball2.speed_y = new_v2y

                    # 速度の二乗を更新
                    ball1.speed_sq = new_v1x * new_v1x + new_v1y * new_v1y
                    ball2.speed_sq = new_v2x * new_v2x + new_v2y * new_v2y

            # 位置補正
            overlap = radii_sum - dist
            if overlap > 0:
                correction = overlap * 0.4  # 補正係数
                correction_x = correction * nx
                correction_y = correction * ny

                ball1.x += correction_x
                ball1.y += correction_y
                ball2.x -= correction_x
                ball2.y -= correction_y

                ball1._bbox_dirty = True
                ball2._bbox_dirty = True


def _loop(
    lcd: ST7789V,
    background: Image.Image,
    balls: List[Ball],
    fps_counter: FpsCounter,
    font,
    target_fps: float,
    tracker: Optional[BenchmarkTracker] = None,
):
    """Main animation loop relying on driver-level optimization."""
    target_duration = 1.0 / target_fps
    last_frame_time = time.time()
    frame_count = 0

    inv_substeps = 1.0 / PHYSICS_SUBSTEPS
    screen_width = lcd.size.width
    screen_height = lcd.size.height

    if tracker:
        tracker.start()

    while True:
        frame_count += 1
        current_time = time.time()
        delta_t = max(
            min(current_time - last_frame_time, target_duration * 2.5),
            target_duration * 0.2,
        )
        last_frame_time = current_time
        sub_delta_t = delta_t * inv_substeps

        for _ in range(PHYSICS_SUBSTEPS):
            for ball in balls:
                ball.update_position(sub_delta_t, screen_width, screen_height)
            _handle_ball_collisions_optimized(balls, frame_count)

        # 描画処理: 毎回背景をコピーして全描画
        # ドライバーレベルの Dirty Rectangle 最適化により、これで十分高速。
        frame_image = background.copy()
        draw = ImageDraw.Draw(frame_image)
        for ball in balls:
            ball.draw(draw)

        fps_counter.update()
        draw_text(
            draw,
            fps_counter.fps_text,
            font,
            x="left",
            y="top",
            width=screen_width,
            height=screen_height,
            color=TEXT_COLOR,
        )

        lcd.display(frame_image)

        if tracker:
            tracker.update()
            if tracker.should_stop():
                break

        wait_time = max(0, last_frame_time + target_duration - time.time())
        if wait_time > 0:
            time.sleep(wait_time)


# --- CLIコマンド ---
@click.command(help="Balls animation")
@click.option(
    "--spi-mhz",
    "-z",
    type=float,
    default=SPI_SPEED_HZ / 1_000_000,
    show_default=True,
    help="SPI speed in MHz",
)
@click.option(
    "--fps",
    "-f",
    type=float,
    default=TARGET_FPS,
    show_default=True,
    help="Target frames per second",
)
@click.option(
    "--num-balls",
    "-n",
    type=int,
    default=3,
    show_default=True,
    help="Number of balls to display",
)
@click.option(
    "--ball-speed",
    "-s",
    type=float,
    default=None,
    help="Absolute speed of balls (pixels/second).",
)
@click.option(
    "--benchmark",
    "-B",
    type=int,
    is_flag=False,
    flag_value=10,
    help="Run benchmark for N seconds (default 10) and report FPS/CPU usage.",
)
@click.option(
    "--rst", type=int, default=25, show_default=True, help="RST PIN"
)
@click.option("--dc", type=int, default=24, show_default=True, help="DC PIN")
@click.option("--bl", type=int, default=23, show_default=True, help="BL PIN")
@click_common_opts(__version__)
def ballanime(
    ctx,
    spi_mhz: float,
    fps: float,
    num_balls: int,
    ball_speed: float,
    benchmark: Optional[int],
    rst,
    dc,
    bl,
    debug,
) -> None:
    """物理ベースのアニメーションデモを実行する。"""
    __log = get_logger(__name__, debug)
    __log.debug(
        "spi_mhz=%s, fps=%s, num_balls=%s, ball_speed=%s, benchmark=%s",
        spi_mhz,
        fps,
        num_balls,
        ball_speed,
        benchmark,
    )
    __log.debug("rst=%s, dc=%s, bl=%s", rst, dc, bl)

    __log.info("fps=%s ... Ctrl+C で終了してください。", fps)

    try:
        with ST7789V(
            speed_hz=int(spi_mhz * 1_000_000),
            pin=SpiPins(rst=rst, dc=dc, bl=bl),
            debug=debug,
        ) as lcd:
            # フォントをロード
            font_large: ImageFont.FreeTypeFont | ImageFont.ImageFont
            font_small: ImageFont.FreeTypeFont | ImageFont.ImageFont
            try:
                font_large = ImageFont.truetype(FONT_PATH, 40)
                font_small = ImageFont.truetype(FONT_PATH, 24)
            except IOError as _e:
                __log.warning("%s: %s: %s", FONT_PATH, type(_e).__name__, _e)
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # 背景画像を生成
            background_image = Image.new(
                "RGB", (lcd.size.width, lcd.size.height)
            )
            draw = ImageDraw.Draw(background_image)
            for y in range(lcd.size.height):
                color = (y % 256, (y * 2) % 256, (y * 3) % 256)
                draw.line((0, y, lcd.size.width, y), fill=color)

            # 静的テキスト（IPアドレスなど）を描画
            ip_address = get_ip_address()
            draw_text(
                draw,
                ip_address,
                font_small,
                x="center",
                y="bottom",
                width=lcd.size.width,
                height=lcd.size.height,
                color=TEXT_COLOR,
            )

            lcd.display(background_image)

            # オブジェクトを初期化
            balls = _initialize_balls_optimized(
                num_balls, lcd.size.width, lcd.size.height, ball_speed
            )
            fps_counter = FpsCounter()

            # ベンチマーク設定
            tracker = None
            if benchmark is not None:
                duration = int(benchmark)
                if duration < 1:
                    __log.warning(
                        "Benchmark duration must be at least 1s. Using default 10s."
                    )
                    duration = 10
                tracker = BenchmarkTracker(duration=duration)

            # メインループを開始
            _loop(
                lcd,
                background_image,
                balls,
                fps_counter,
                font_large,
                fps,
                tracker,
            )

            if tracker:
                res = tracker.get_results()
                print("\n--- Benchmark Results ---")
                print(f"Duration: {res['duration']:.2f}s")
                print(f"Total Frames: {res['total_frames']}")
                print(f"Avg FPS: {res['avg_fps']:.2f}")
                print(f"Avg CPU (ballanime): {res['avg_cpu']:.1f}%")
                print(f"Avg CPU (pigpiod): {res['avg_pigpiod']:.1f}%")
                print("--------------------------\n")

    except KeyboardInterrupt:
        __log.info("\n終了しました。\n")
    except Exception as e:
        __log.error(f"エラーが発生しました: {e}")
        exit(1)
