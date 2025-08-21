#
# (c) 2025 Yoichi Tanibayashi
#
"""
ST7789Vディスプレイで動作する、物理ベースのアニメーションデモ。
最適化されたドライバとユーティリティ関数を使用。
"""
import time
from typing import List, Tuple

import click
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .. import ST7789V
from ..my_logger import get_logger
from ..utils import (
    merge_bboxes, optimize_dirty_regions, clamp_region, 
    get_ip_address, draw_text
)

log = get_logger(__name__)

# --- 定数 ---
SPI_SPEED_HZ = 16000000
TARGET_FPS = 30.0
BALL_RADIUS = 20
FONT_PATH = "Firge-Regular.ttf"
TEXT_COLOR = (255, 255, 255)
FPS_UPDATE_INTERVAL = 0.2

# --- 描画オブジェクトクラス ---
class Ball:
    """アニメーションするボールの状態と振る舞いを管理するクラス。"""
    def __init__(self, x, y, radius, speed_x, speed_y, fill_color):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)
        self.fill_color = fill_color
        self.prev_bbox = None

    def update_position(self, delta_t, screen_width, screen_height):
        self.x += self.speed_x * delta_t
        self.y += self.speed_y * delta_t
        if self.x - self.radius < 0:
            self.x = self.radius
            self.speed_x = -self.speed_x
        if self.x + self.radius >= screen_width:
            self.x = screen_width - self.radius - 1
            self.speed_x = -self.speed_x
        if self.y - self.radius < 0:
            self.y = self.radius
            self.speed_y = -self.speed_y
        if self.y + self.radius >= screen_height:
            self.y = screen_height - self.radius - 1
            self.speed_y = -self.speed_y

    def get_bbox(self):
        return (int(self.x - self.radius), int(self.y - self.radius),
                int(self.x + self.radius), int(self.y + self.radius))

    def draw(self, image_buffer):
        draw = ImageDraw.Draw(image_buffer)
        bbox = self.get_bbox()
        draw.ellipse(bbox, fill=self.fill_color, outline=self.fill_color)
        self.prev_bbox = bbox

class FpsCounter:
    """FPSの計算と表示を管理する。"""
    def __init__(self):
        self.frame_count = 0
        self.last_update_time = time.time()
        self.fps_text = "FPS: --"

    def update(self) -> bool:
        """FPSを更新し、表示テキストが変更されたかを返す。"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_update_time
        if elapsed >= FPS_UPDATE_INTERVAL:
            fps = self.frame_count / elapsed
            self.fps_text = f"FPS: {fps:.0f}"
            self.frame_count = 0
            self.last_update_time = current_time
            return True
        return False

# --- ヘルパー関数 ---
def _initialize_balls(num_balls: int, width: int, height: int, ball_speed: float) -> List[Ball]:
    balls = []
    for _ in range(num_balls):
        x = np.random.randint(BALL_RADIUS, width - BALL_RADIUS)
        y = np.random.randint(BALL_RADIUS, height - BALL_RADIUS)
        angle = np.random.rand() * 2 * np.pi
        speed_x = (ball_speed or 300.0) * np.cos(angle)
        speed_y = (ball_speed or 200.0) * np.sin(angle)
        fill_color = tuple(np.random.randint(0, 256, 3))
        balls.append(Ball(x, y, BALL_RADIUS, speed_x, speed_y, fill_color))
    return balls

def _main_loop(lcd: ST7789V, background: Image.Image, balls: List[Ball], 
               fps_counter: FpsCounter, font: ImageFont.ImageFont, target_fps: float):
    last_frame_time = time.time()
    target_duration = 1.0 / target_fps
    hud_layer = Image.new("RGBA", (lcd.width, lcd.height), (0, 0, 0, 0))
    hud_draw = ImageDraw.Draw(hud_layer)
    prev_fps_bbox = None

    while True:
        frame_start_time = time.time()
        delta_t = frame_start_time - last_frame_time
        last_frame_time = frame_start_time

        new_frame_image = background.copy()
        dirty_regions = []

        for ball in balls:
            prev_bbox = ball.prev_bbox
            ball.update_position(delta_t, lcd.width, lcd.height)
            curr_bbox = ball.get_bbox()
            dirty_region = merge_bboxes(prev_bbox, curr_bbox)
            if dirty_region:
                # Add padding to the dirty region to prevent ghosting
                padded_dirty_region = (
                    dirty_region[0] - 2,  # x0 - padding
                    dirty_region[1] - 2,  # y0 - padding
                    dirty_region[2] + 2,  # x1 + padding
                    dirty_region[3] + 2   # y1 + padding
                )
                dirty_regions.append(clamp_region(padded_dirty_region, lcd.width, lcd.height))
            ball.draw(new_frame_image)

        if fps_counter.update():
            # Expand prev_fps_bbox before clearing
            if prev_fps_bbox:
                expanded_prev_fps_bbox = (
                    prev_fps_bbox[0] - 4,
                    prev_fps_bbox[1] - 6,
                    prev_fps_bbox[2] + 4,
                    prev_fps_bbox[3] + 6
                )
                hud_draw.rectangle(expanded_prev_fps_bbox, fill=(0, 0, 0, 0))

            # Draw new text and get its bbox
            current_fps_bbox = draw_text(hud_draw, fps_counter.fps_text, font, 
                                      x='left', y='top',
                                      width=lcd.width, height=lcd.height, 
                                      color=TEXT_COLOR)
            
            # Expand current_fps_bbox before adding to dirty_regions
            expanded_current_fps_bbox = (
                current_fps_bbox[0] - 4,
                current_fps_bbox[1] - 6,
                current_fps_bbox[2] + 4,
                current_fps_bbox[3] + 6
            )
            dirty_regions.append(expanded_current_fps_bbox)
            prev_fps_bbox = current_fps_bbox # Store the unexpanded bbox for next frame's clearing

        frame_rgba = new_frame_image.convert("RGBA")
        frame_rgba.alpha_composite(hud_layer)
        final_frame = frame_rgba.convert("RGB")

        if dirty_regions:
            optimized = optimize_dirty_regions(dirty_regions, max_regions=8)
            for r in optimized:
                lcd.display_region(final_frame, *r)

        elapsed = time.time() - frame_start_time
        if elapsed < target_duration:
            time.sleep(target_duration - elapsed)

# --- CLIコマンド ---
@click.command()
@click.option('--speed', default=SPI_SPEED_HZ, type=int, help='SPI speed in Hz', show_default=True)
@click.option('--fps', default=TARGET_FPS, type=float, help='Target frames per second', show_default=True)
@click.option('--num-balls', default=3, type=int, help='Number of balls to display', show_default=True)
@click.option('--ball-speed', default=None, type=float, help='Absolute speed of balls (pixels/second).')
def test(speed: int, fps: float, num_balls: int, ball_speed: float):
    """物理ベースのアニメーションデモを実行する。"""
    log.info(f"最適化モードでフレームレート約{fps}FPSで動作します... Ctrl+C で終了してください。")

    try:
        with ST7789V(speed_hz=speed) as lcd:
            # フォントをロード
            try:
                font_large = ImageFont.truetype(FONT_PATH, 40)
                font_small = ImageFont.truetype(FONT_PATH, 24)
            except IOError:
                log.warning(f"警告: '{FONT_PATH}' が見つかりません。デフォルトフォントを使用します。")
                font_large = ImageFont.load_default()
                font_small = ImageFont.load_default()

            # 背景画像を生成
            background_image = Image.new("RGB", (lcd.width, lcd.height))
            draw = ImageDraw.Draw(background_image)
            for y in range(lcd.height):
                color = (y % 256, (y*2) % 256, (y*3) % 256)
                draw.line((0, y, lcd.width, y), fill=color)

            # 静的テキスト（IPアドレスなど）を描画
            ip_address = get_ip_address()
            draw_text(draw, ip_address, font_small, 
                      x='center', y='bottom',
                      width=lcd.width, height=lcd.height, 
                      color=TEXT_COLOR)
            
            lcd.display(background_image)

            # オブジェクトを初期化
            balls = _initialize_balls(num_balls, lcd.width, lcd.height, ball_speed)
            fps_counter = FpsCounter()
            
            # メインループを開始
            _main_loop(lcd, background_image, balls, fps_counter, font_large, fps)

    except KeyboardInterrupt:
        log.info("\n終了しました。\n")
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        exit(1)