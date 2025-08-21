#
# (c) 2025 Yoichi Tanibayashi
#
"""
ST7789Vディスプレイで動作する、物理ベースのアニメーションデモ。
最適化されたドライバとユーティリティ関数を使用。
"""
import time
from typing import List

import click
import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .. import ST7789V
from ..my_logger import get_logger
from ..utils import merge_bboxes, optimize_dirty_regions, clamp_region

log = get_logger(__name__)

# --- 定数 ---
SPI_SPEED_HZ = 16000000
TARGET_FPS = 30.0
BALL_RADIUS = 20
BALL_INITIAL_SPEED_X = 300.0
BALL_INITIAL_SPEED_Y = 200.0
BALL_FILL_COLOR = (255, 255, 0)
BALL_OUTLINE_COLOR = (255, 255, 255)
FPS_FONT_PATH = "Firge-Regular.ttf"
FPS_FONT_SIZE = 50
FPS_TEXT_COLOR = (255, 255, 255)
FPS_UPDATE_INTERVAL = 0.2
FPS_AREA_PADDING = 5

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
        """時間経過に基づきボールの位置を更新し、画面境界で反射させる。"""
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
        """現在のボールの位置を囲むバウンディングボックスを返す。"""
        return (
            int(self.x - self.radius), int(self.y - self.radius),
            int(self.x + self.radius), int(self.y + self.radius)
        )

    def draw(self, image_buffer):
        """指定されたPIL Imageバッファにボールを描画する。"""
        draw = ImageDraw.Draw(image_buffer)
        bbox = self.get_bbox()
        draw.ellipse(bbox, fill=self.fill_color, outline=self.fill_color)
        self.prev_bbox = bbox


class FpsCounter:
    """FPS（Frames Per Second）の計算と表示を管理するクラス。"""
    def __init__(self, lcd, fps_layer):
        try:
            self.font = ImageFont.truetype(FPS_FONT_PATH, FPS_FONT_SIZE)
            log.info(f"'{FPS_FONT_PATH}' フォントを読み込みました。")
        except IOError:
            log.warning(f"警告: '{FPS_FONT_PATH}' が見つかりません。デフォルトフォントを使用します。")
            self.font = ImageFont.load_default()

        padding = FPS_AREA_PADDING
        pos = (padding, padding)
        base_bbox = ImageDraw.Draw(fps_layer).textbbox((0,0), "FPS: 999", font=self.font)
        box_width = base_bbox[2] - base_bbox[0] + (padding * 2)
        box_height = base_bbox[3] - base_bbox[1] + (padding * 2)
        
        self.bbox = (pos[0], pos[1], pos[0] + box_width, pos[1] + box_height)
        self.draw_offset = (padding - base_bbox[0], padding - base_bbox[1])

        self.frame_count = 0
        self.last_update_time = time.time()

    def update_and_draw(self, fps_layer):
        """FPSを更新し、一定間隔で指定レイヤーに再描画する。"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_update_time

        if elapsed >= FPS_UPDATE_INTERVAL:
            fps = self.frame_count / elapsed
            fps_text = f"FPS: {fps:.0f}"

            # FPSレイヤーをクリアして文字を再描画
            fps_layer.paste((0,0,0,0), self.bbox)
            draw = ImageDraw.Draw(fps_layer)
            draw.text((self.bbox[0] + self.draw_offset[0], self.bbox[1] + self.draw_offset[1]),
                      fps_text, font=self.font, fill=FPS_TEXT_COLOR)

            self.frame_count = 0
            self.last_update_time = current_time
            return self.bbox

        return None

# --- ヘルパー関数 ---
def _initialize_balls(num_balls: int, width: int, height: int, ball_speed: float) -> List[Ball]:
    """指定された数のBallオブジェクトを初期化してリストで返す。"""
    balls = []
    for _ in range(num_balls):
        x = np.random.randint(BALL_RADIUS, width - BALL_RADIUS)
        y = np.random.randint(BALL_RADIUS, height - BALL_RADIUS)

        if ball_speed is not None:
            angle = np.random.rand() * 2 * np.pi
            speed_x = ball_speed * np.cos(angle)
            speed_y = ball_speed * np.sin(angle)
        else:
            speed_x = BALL_INITIAL_SPEED_X * (1 + (np.random.rand() - 0.5) * 0.5)
            speed_y = BALL_INITIAL_SPEED_Y * (1 + (np.random.rand() - 0.5) * 0.5)

        fill_color = (
            np.random.randint(0, 256),
            np.random.randint(0, 256),
            np.random.randint(0, 256)
        )
        balls.append(Ball(x, y, BALL_RADIUS, speed_x, speed_y, fill_color))
    return balls

def _main_loop(lcd: ST7789V, background: Image.Image, balls: List[Ball], fps_layer: Image.Image, fps_counter: FpsCounter, target_fps: float):
    """アニメーションのメインループを実行する。"""
    last_frame_time = time.time()
    target_duration = 1.0 / target_fps

    while True:
        frame_start_time = time.time()
        delta_t = frame_start_time - last_frame_time
        last_frame_time = frame_start_time

        new_frame_image = background.copy()
        dirty_regions = []

        # ボールの更新と描画
        for ball in balls:
            prev_bbox = ball.prev_bbox
            ball.update_position(delta_t, lcd.width, lcd.height)
            curr_bbox = ball.get_bbox()

            dirty_region = merge_bboxes(prev_bbox, curr_bbox)
            if dirty_region:
                dirty_region = clamp_region((
                    dirty_region[0] - 1, dirty_region[1] - 1,
                    dirty_region[2] + 1, dirty_region[3] + 1,
                ), lcd.width, lcd.height)
                dirty_regions.append(dirty_region)

            ball.draw(new_frame_image)

        # FPS更新
        fps_dirty_bbox = fps_counter.update_and_draw(fps_layer)
        if fps_dirty_bbox:
            dirty_regions.append(clamp_region(fps_dirty_bbox, lcd.width, lcd.height))

        # HUDレイヤーをフレームに合成
        frame_rgba = new_frame_image.convert("RGBA")
        frame_rgba.alpha_composite(fps_layer)
        final_frame = frame_rgba.convert("RGB")

        # ダーティ領域を最適化してディスプレイに転送
        if dirty_regions:
            optimized_regions = optimize_dirty_regions(dirty_regions, max_regions=6)
            for region in optimized_regions:
                if region[2] > region[0] and region[3] > region[1]:
                    lcd.display_region(final_frame, region[0], region[1], region[2], region[3])

        # フレームレート制御
        elapsed_time = time.time() - frame_start_time
        sleep_duration = target_duration - elapsed_time
        if sleep_duration > 0:
            time.sleep(sleep_duration)

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
            # 背景画像を生成
            background_image = Image.new("RGB", (lcd.width, lcd.height))
            draw = ImageDraw.Draw(background_image)
            for y in range(lcd.height):
                color = (y % 256, (y*2) % 256, (y*3) % 256)
                draw.line((0, y, lcd.width, y), fill=color)
            lcd.display(background_image)

            # オブジェクトを初期化
            balls = _initialize_balls(num_balls, lcd.width, lcd.height, ball_speed)
            fps_layer = Image.new("RGBA", (lcd.width, lcd.height), (0,0,0,0))
            fps_counter = FpsCounter(lcd, fps_layer)
            
            # メインループを開始
            _main_loop(lcd, background_image, balls, fps_layer, fps_counter, fps)

    except KeyboardInterrupt:
        log.info("\n終了しました。\n")
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        exit(1)
