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

import cairo
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
from ..utils.performance_core import RegionOptimizer
from ..utils.process_utils import (
    calculate_average_memory_usage,
    format_memory_usage,
    get_ballanime_pigpiod_pids,
)
from ..utils.sprite import CircleSprite

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
class Ball(CircleSprite):
    """計算最適化版ボールクラス（見た目は同じ）"""

    __slots__ = (
        "speed_x",
        "speed_y",
        "fill_color",
        "speed_sq",
    )

    def __init__(self, x, y, radius, speed, angle, fill_color):
        super().__init__(cx=float(x), cy=float(y), radius=radius)

        # 三角関数計算を事前実行
        cos_a, sin_a = fast_cos_sin(angle)
        self.speed_x = speed * cos_a
        self.speed_y = speed * sin_a
        self.speed_sq = speed * speed  # 速度の二乗を事前計算

        self.fill_color = fill_color

    def update_position(self, delta_t, screen_width, screen_height):
        """位置更新（計算最適化版）"""
        # インライン計算で関数呼び出しオーバーヘッド削減
        new_cx = self.cx + self.speed_x * delta_t
        new_cy = self.cy + self.speed_y * delta_t

        # 境界チェック（分岐予測最適化）
        r = self.radius
        width_limit = screen_width - r
        height_limit = screen_height - r

        # X軸境界チェック
        if new_cx <= r:
            new_cx = r
            self.speed_x = -self.speed_x
        elif new_cx >= width_limit:
            new_cx = width_limit - 1
            self.speed_x = -self.speed_x

        # Y軸境界チェック
        if new_cy <= r:
            new_cy = r
            self.speed_y = -self.speed_y
        elif new_cy >= height_limit:
            new_cy = height_limit - 1
            self.speed_y = -self.speed_y

        # 位置更新時に速度の二乗も更新
        self.speed_sq = (
            self.speed_x * self.speed_x + self.speed_y * self.speed_y
        )

        # 位置が変わったら更新
        self.cx = new_cx
        self.cy = new_cy

    def update(self, delta_t: float):
        """Spriteインターフェース用"""
        pass

    def draw(self, draw: ImageDraw.ImageDraw):
        """描画処理"""
        # Sprite.bbox を利用 (左上, 左上, 右下, 右下)
        draw.ellipse(self.bbox, fill=self.fill_color, outline=self.fill_color)


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
        self.mem_ballanime_samples: List[int] = []
        self.mem_pigpiod_samples: List[int] = []

        # pigpiod プロセスを特定
        _, pigpiod_pid = get_ballanime_pigpiod_pids()
        if pigpiod_pid:
            try:
                self.pigpiod_process = psutil.Process(pigpiod_pid)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                self.pigpiod_process = None

    def start(self):
        self.start_time = time.time()
        # 初回のCPU負荷計測（基準値）
        self.process.cpu_percent(interval=None)
        if self.pigpiod_process:
            try:
                self.pigpiod_process.cpu_percent(interval=None)
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

    def update(self):
        if self.start_time is None:
            return

        self.total_frames += 1

        # 1秒ごとにCPU負荷とメモリ使用量をサンプリング
        elapsed = time.time() - self.start_time
        if int(elapsed) > len(self.cpu_samples):
            try:
                self.cpu_samples.append(
                    self.process.cpu_percent(interval=None)
                )
                self.mem_ballanime_samples.append(
                    self.process.memory_info().rss
                )

                if self.pigpiod_process:
                    self.pigpiod_samples.append(
                        self.pigpiod_process.cpu_percent(interval=None)
                    )
                    self.mem_pigpiod_samples.append(
                        self.pigpiod_process.memory_info().rss
                    )
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                pass

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

        # 平均メモリ使用量の算出とフォーマット
        avg_mem_ballanime = calculate_average_memory_usage(
            self.mem_ballanime_samples
        )
        avg_mem_pigpiod = calculate_average_memory_usage(
            self.mem_pigpiod_samples
        )

        return {
            "duration": elapsed,
            "avg_fps": avg_fps,
            "avg_cpu": avg_cpu,
            "avg_pigpiod": avg_pigpiod,
            "avg_mem_ballanime": format_memory_usage(avg_mem_ballanime),
            "avg_mem_pigpiod": format_memory_usage(avg_mem_pigpiod),
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
                dx = x - existing_ball.cx
                dy = y - existing_ball.cy
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

                ball1.cx += sep_x
                ball1.cy += sep_y
                ball2.cx -= sep_x
                ball2.cy -= sep_y
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

                ball1.cx += correction_x
                ball1.cy += correction_y
                ball2.cx -= correction_x
                ball2.cy -= correction_y


def pil_to_cairo_surface(pil_image: Image.Image) -> cairo.ImageSurface:
    """PIL画像をCairo ImageSurface (ARGB32) に変換する。"""
    if pil_image.mode != "RGBA":
        pil_image = pil_image.convert("RGBA")

    width, height = pil_image.size
    data = np.array(pil_image)
    # RGB(A) to BGRA
    data = data[:, :, [2, 1, 0, 3]]

    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    buf = surface.get_data()
    buf[:] = data.tobytes()
    surface.mark_dirty()
    return surface


def cairo_surface_to_pil(
    surface: cairo.ImageSurface, region: tuple | None = None
) -> Image.Image:
    """Cairo ImageSurface (ARGB32) を PIL画像 (RGB) に変換する。"""
    width = surface.get_width()
    height = surface.get_height()
    stride = surface.get_stride()

    # Get buffer and wrap it in a numpy array, accounting for stride
    buf = surface.get_data()
    raw_data = np.frombuffer(buf, dtype=np.uint8).reshape(height, stride)
    # Extract only the active pixel data (4 bytes per pixel for ARGB32)
    # and reshape to 3D (height, width, 4)
    data = raw_data[:, : width * 4].reshape(height, width, 4)

    if region:
        x1, y1, x2, y2 = region
        # Ensure coordinates are within bounds
        x1, y1 = max(0, x1), max(0, y1)
        x2, y2 = min(width, x2), min(height, y2)
        if x1 >= x2 or y1 >= y2:
            return Image.new("RGB", (1, 1), (0, 0, 0))
        # Use copy to detach from the potentially changing cairo buffer
        target_data = data[y1:y2, x1:x2, :].copy()
    else:
        target_data = data.copy()

    # Cairo FORMAT_ARGB32 is BGRA in little-endian.
    # BGRA to RGB: select channels 2, 1, 0
    return Image.fromarray(target_data[:, :, [2, 1, 0]], "RGB")


def _loop(
    lcd: ST7789V,
    background: Image.Image,
    balls: List[Ball],
    fps_counter: FpsCounter,
    font,
    target_fps: float,
    mode: str = "simple",
    tracker: Optional[BenchmarkTracker] = None,
):
    """Main animation loop."""
    target_duration = 1.0 / target_fps
    last_frame_time = time.time()
    frame_count = 0

    inv_substeps = 1.0 / PHYSICS_SUBSTEPS
    screen_width = lcd.size.width
    screen_height = lcd.size.height

    if tracker:
        tracker.start()

    # 描画バッファ
    frame_image = background.copy()

    # Cairo初期化
    cairo_surface = None
    cairo_ctx = None
    background_surface = None
    if "cairo" in mode:
        cairo_surface = cairo.ImageSurface(
            cairo.FORMAT_ARGB32, screen_width, screen_height
        )
        cairo_ctx = cairo.Context(cairo_surface)
        background_surface = pil_to_cairo_surface(background)

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

        if mode == "simple":
            # 描画処理: 毎回背景をコピーして全描画
            frame_image.paste(background)
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

        elif mode == "optimized":
            dirty_regions = []
            for ball in balls:
                region = ball.get_dirty_region()
                if region:
                    dirty_regions.append(region)

            fps_updated = fps_counter.update()
            if fps_updated:
                # FPSテキスト領域 (左上)
                dirty_regions.append((0, 0, 100, 40))

            merged_regions = RegionOptimizer.merge_regions(dirty_regions)

            # 重要：マージ後の領域が FPS エリア (0, 0, 100, 40) と重なる場合、
            # 背景復元でテキストが消えているため、再描画が必要。
            fps_area_invaded = any(
                (rx < 100 and ry < 40 and rx + rw > 0 and ry + rh > 0)
                for rx, ry, rw, rh in merged_regions
            )

            if merged_regions:
                # 1. Dirty Region を背景で修復 (完全に初期化)
                for rx, ry, rw, rh in merged_regions:
                    x1, y1 = max(0, rx), max(0, ry)
                    x2, y2 = (
                        min(screen_width, rx + rw),
                        min(screen_height, ry + rh),
                    )
                    if x1 >= x2 or y1 >= y2:
                        continue
                    patch = background.crop((x1, y1, x2, y2))
                    frame_image.paste(patch, (x1, y1))

                # 2. その領域に関連するオブジェクトを再描画 (一括)
                draw = ImageDraw.Draw(frame_image)
                for ball in balls:
                    ball.draw(draw)

                # 3. FPSテキストの再描画 (必要なら)
                if fps_updated or fps_area_invaded:
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

                # 4. ディスプレイ更新
                for rx, ry, rw, rh in merged_regions:
                    x1, y1 = max(0, rx), max(0, ry)
                    x2, y2 = (
                        min(screen_width, rx + rw),
                        min(screen_height, ry + rh),
                    )
                    if x1 >= x2 or y1 >= y2:
                        continue

                    # 正しいシグネチャで呼び出し: display_region(image, x0, y0, x1, y1)
                    lcd.display_region(frame_image, x1, y1, x2, y2)

            for ball in balls:
                ball.record_current_bbox()

        elif mode == "cairo":
            # Cairoオブジェクトが初期化されていることを保証
            assert cairo_ctx is not None
            assert cairo_surface is not None
            assert background_surface is not None

            # 背景描画
            cairo_ctx.set_source_surface(background_surface, 0, 0)
            cairo_ctx.paint()

            # ボール描画 (アンチエイリアスあり)
            for ball in balls:
                r, g, b = [c / 255.0 for c in ball.fill_color]
                cairo_ctx.set_source_rgb(r, g, b)
                cairo_ctx.arc(ball.cx, ball.cy, ball.radius, 0, TWO_PI)
                cairo_ctx.fill()

            # PIL画像に変換
            frame_image = cairo_surface_to_pil(cairo_surface)
            draw = ImageDraw.Draw(frame_image)

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

        elif mode == "cairo-optimized":
            # Cairoオブジェクトが初期化されていることを保証
            assert cairo_ctx is not None
            assert cairo_surface is not None
            assert background_surface is not None

            dirty_regions = []
            for ball in balls:
                region = ball.get_dirty_region()
                if region:
                    dirty_regions.append(region)

            fps_updated = fps_counter.update()
            if fps_updated:
                dirty_regions.append((0, 0, 100, 40))

            merged_regions = RegionOptimizer.merge_regions(dirty_regions)

            # 重要：マージ後の領域が FPS エリア (0, 0, 100, 40) と重なる場合、
            # 背景復元でテキストが消えているため、再描画が必要。
            fps_area_invaded = any(
                (rx < 100 and ry < 40 and rx + rw > 0 and ry + rh > 0)
                for rx, ry, rw, rh in merged_regions
            )

            if merged_regions:
                for rx, ry, rw, rh in merged_regions:
                    x1, y1 = max(0, rx), max(0, ry)
                    x2, y2 = (
                        min(screen_width, rx + rw),
                        min(screen_height, ry + rh),
                    )
                    if x1 >= x2 or y1 >= y2:
                        continue

                    # 1. Cairo側での描画
                    cairo_ctx.save()
                    cairo_ctx.rectangle(x1, y1, x2 - x1, y2 - y1)
                    cairo_ctx.clip()

                    # 完全に背景で塗りつぶしてから描画 (重ね塗りを排除)
                    cairo_ctx.set_source_surface(background_surface, 0, 0)
                    cairo_ctx.paint()

                    for ball in balls:
                        r, g, b = [c / 255.0 for c in ball.fill_color]
                        cairo_ctx.set_source_rgb(r, g, b)
                        cairo_ctx.arc(
                            ball.cx, ball.cy, ball.radius, 0, TWO_PI
                        )
                        cairo_ctx.fill()

                    cairo_ctx.restore()

                    # 2. その領域を PIL画像に変換して全画面バッファに反映
                    region_image = cairo_surface_to_pil(
                        cairo_surface, (x1, y1, x2, y2)
                    )
                    frame_image.paste(region_image, (x1, y1))

                # 3. テキストの再描画 (必要なら)
                # 全てのリージョンの再描画が終わった後に、テキストを重ねる。
                if fps_updated or fps_area_invaded:
                    draw_text(
                        ImageDraw.Draw(frame_image),
                        fps_counter.fps_text,
                        font,
                        x="left",
                        y="top",
                        width=screen_width,
                        height=screen_height,
                        color=TEXT_COLOR,
                    )

                # 4. ディスプレイ更新
                for rx, ry, rw, rh in merged_regions:
                    x1, y1 = max(0, rx), max(0, ry)
                    x2, y2 = (
                        min(screen_width, rx + rw),
                        min(screen_height, ry + rh),
                    )
                    if x1 >= x2 or y1 >= y2:
                        continue
                    lcd.display_region(frame_image, x1, y1, x2, y2)

            for ball in balls:
                ball.record_current_bbox()

        else:
            __log.warning(f"Mode {mode} unknown, using simple.")
            frame_image.paste(background)
            draw = ImageDraw.Draw(frame_image)
            for ball in balls:
                ball.draw(draw)
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
    "--mode",
    "-m",
    type=click.Choice(
        ["simple", "optimized", "cairo", "cairo-optimized"],
        case_sensitive=False,
    ),
    default="simple",
    show_default=True,
    help="Optimization/Rendering mode",
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
    mode: str,
    rst,
    dc,
    bl,
    debug,
) -> None:
    """物理ベースのアニメーションデモを実行する。"""
    __log = get_logger(__name__, debug)
    __log.debug(
        "spi_mhz=%s, fps=%s, num_balls=%s, ball_speed=%s, benchmark=%s, mode=%s",
        spi_mhz,
        fps,
        num_balls,
        ball_speed,
        benchmark,
        mode,
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
                mode,
                tracker,
            )

            if tracker:
                res = tracker.get_results()
                print("\n--- Benchmark Results ---")
                print(f"Mode: {mode}")
                print(f"Num Balls: {num_balls}")
                print(f"Target FPS: {fps}")
                print(f"SPI Speed: {spi_mhz} MHz")
                print("-" * 25)
                print(f"Duration: {res['duration']:.2f}s")
                print(f"Total Frames: {res['total_frames']}")
                print(f"Avg FPS: {res['avg_fps']:.2f}")
                print(f"Avg CPU (ballanime): {res['avg_cpu']:.1f}%")
                print(f"Avg CPU (pigpiod): {res['avg_pigpiod']:.1f}%")
                print(f"Avg Mem (ballanime): {res['avg_mem_ballanime']}")
                print(f"Avg Mem (pigpiod): {res['avg_mem_pigpiod']}")
                print("--------------------------\n")

                # レポートの保存
                report_file = "ballanime-report.md"
                file_exists = os.path.exists(report_file)
                with open(report_file, "a") as f:
                    if not file_exists:
                        f.write("# Ballanime Benchmark Report\n\n")
                        f.write(
                            "| Date | Mode | Balls | Target FPS | SPI | Avg FPS | CPU (App) | CPU (pigpiod) | Mem (App) | Mem (pig) |\n"
                        )
                        f.write(
                            "|------|------|-------|------------|-----|---------|-----------|--------------|-----------|-----------|\n"
                        )

                    timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
                    f.write(
                        f"| {timestamp} | {mode} | {num_balls} | {fps} | {spi_mhz}M | {res['avg_fps']:.2f} | {res['avg_cpu']:.1f}% | {res['avg_pigpiod']:.1f}% | {res['avg_mem_ballanime']} | {res['avg_mem_pigpiod']} |\n"
                    )
                __log.info(f"Report saved to {report_file}")

    except KeyboardInterrupt:
        __log.info("\n終了しました。\n")
    except Exception as e:
        __log.error(f"エラーが発生しました: {e}")
        exit(1)
