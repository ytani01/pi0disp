# -*- coding: utf-8 -*-
"""
ST7789Vディスプレイで動作する、物理ベースのアニメーションデモ。
"""
import time
import click
from PIL import Image, ImageDraw, ImageFont
import numpy as np

from .. import ST7789V
from ..my_logger import get_logger
from ..utils import pil_to_rgb565_bytes, merge_bboxes

log = get_logger(__name__)

# --- 設定クラス ---
class CONFIG:
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
        return (
            int(self.x - self.radius), int(self.y - self.radius),
            int(self.x + self.radius), int(self.y + self.radius)
        )

    def draw(self, image_buffer):
        draw = ImageDraw.Draw(image_buffer)
        bbox = self.get_bbox()
        # draw.ellipse(bbox, fill=self.fill_color, outline=CONFIG.BALL_OUTLINE_COLOR)
        draw.ellipse(bbox, fill=self.fill_color, outline=self.fill_color)
        self.prev_bbox = bbox


class FpsCounter:
    def __init__(self, lcd, fps_layer):
        try:
            self.font = ImageFont.truetype(CONFIG.FPS_FONT_PATH, CONFIG.FPS_FONT_SIZE)
            log.info(f"'{CONFIG.FPS_FONT_PATH}' フォントを読み込みました。")
        except IOError:
            log.warning(f"警告: '{CONFIG.FPS_FONT_PATH}' が見つかりません。デフォルトフォントを使用します。")
            self.font = ImageFont.load_default()

        padding = CONFIG.FPS_AREA_PADDING
        pos = (padding, padding)
        base_bbox = ImageDraw.Draw(fps_layer).textbbox((0,0), "FPS: 999", font=self.font)
        box_width = base_bbox[2] - base_bbox[0] + (padding * 2)
        box_height = base_bbox[3] - base_bbox[1] + (padding * 2)
        
        self.bbox = (pos[0], pos[1], pos[0] + box_width, pos[1] + box_height)
        self.draw_offset = (padding - base_bbox[0], padding - base_bbox[1])

        self.frame_count = 0
        self.last_update_time = time.time()

    def update_and_draw(self, fps_layer):
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_update_time

        if elapsed >= CONFIG.FPS_UPDATE_INTERVAL:
            fps = self.frame_count / elapsed
            fps_text = f"FPS: {fps:.0f}"

            # --- HUD処理: FPSレイヤーをクリアして文字を再描画 ---
            fps_layer.paste((0,0,0,0), self.bbox)
            draw = ImageDraw.Draw(fps_layer)
            draw.text((self.bbox[0] + self.draw_offset[0], self.bbox[1] + self.draw_offset[1]),
                      fps_text, font=self.font, fill=CONFIG.FPS_TEXT_COLOR)

            self.frame_count = 0
            self.last_update_time = current_time
            return self.bbox

        return None


@click.command()
@click.option('--speed', default=CONFIG.SPI_SPEED_HZ, type=int, help='SPI speed in Hz', show_default=True)
@click.option('--fps', default=CONFIG.TARGET_FPS, type=float, help='Target frames per second', show_default=True)
@click.option('--num-balls', default=3, type=int, help='Number of balls to display', show_default=True)
@click.option('--ball-speed', default=None, type=float, help='Absolute speed of balls (pixels/second).')
def test(speed, fps, num_balls, ball_speed):
    CONFIG.SPI_SPEED_HZ = speed
    CONFIG.TARGET_FPS = fps

    log.info(f"フレームレートを約{CONFIG.TARGET_FPS}FPSに制限します... Ctrl+C で終了してください。")

    try:
        with ST7789V(speed_hz=CONFIG.SPI_SPEED_HZ) as lcd:
            initial_background_image = Image.new("RGB", (lcd.width, lcd.height))
            draw = ImageDraw.Draw(initial_background_image)
            for y in range(lcd.height):
                color = (y % 256, (y*2) % 256, (y*3) % 256)
                draw.line((0, y, lcd.width, y), fill=color)
            
            lcd.display(initial_background_image)

            balls = []
            for i in range(num_balls):
                x = np.random.randint(CONFIG.BALL_RADIUS, lcd.width - CONFIG.BALL_RADIUS)
                y = np.random.randint(CONFIG.BALL_RADIUS, lcd.height - CONFIG.BALL_RADIUS)

                if ball_speed is not None:
                    angle = np.random.rand() * 2 * np.pi
                    speed_x = ball_speed * np.cos(angle)
                    speed_y = ball_speed * np.sin(angle)
                else:
                    speed_x = CONFIG.BALL_INITIAL_SPEED_X * (1 + (np.random.rand() - 0.5) * 0.5)
                    speed_y = CONFIG.BALL_INITIAL_SPEED_Y * (1 + (np.random.rand() - 0.5) * 0.5)

                fill_color = (np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256))
                balls.append(Ball(x, y, CONFIG.BALL_RADIUS, speed_x, speed_y, fill_color))

            # --- HUD処理: FPS用HUDレイヤーを作成 ---
            fps_layer = Image.new("RGBA", (lcd.width, lcd.height), (0,0,0,0))
            fps_counter = FpsCounter(lcd, fps_layer)
            
            last_frame_time = time.time()
            target_duration = 1.0 / CONFIG.TARGET_FPS

            while True:
                frame_start_time = time.time()
                delta_t = frame_start_time - last_frame_time
                last_frame_time = frame_start_time

                new_frame_image = initial_background_image.copy()
                dirty_regions = []

                # --- ボール描画 ---
                for ball in balls:
                    prev_bbox_before_update = ball.prev_bbox
                    ball.update_position(delta_t, lcd.width, lcd.height)
                    curr_bbox_after_update = ball.get_bbox()

                    dirty_region = merge_bboxes(prev_bbox_before_update, curr_bbox_after_update)
                    if dirty_region:
                        dirty_region = (
                            max(0, dirty_region[0] - 1), max(0, dirty_region[1] - 1),
                            min(lcd.width, dirty_region[2] + 1), min(lcd.height, dirty_region[3] + 1),
                        )
                        dirty_regions.append(dirty_region)

                    ball.draw(new_frame_image)

                # --- HUD処理: FPS更新（HUDレイヤーに描画） ---
                fps_dirty_bbox = fps_counter.update_and_draw(fps_layer)
                if fps_dirty_bbox:
                    dirty_regions.append(fps_dirty_bbox)

                # --- HUD処理: HUDレイヤーをフレームに合成 ---
                frame_rgba = new_frame_image.convert("RGBA")
                frame_rgba.alpha_composite(fps_layer)

                # --- LCDへ転送 ---
                for dirty_bbox in dirty_regions:
                    region_to_send = frame_rgba.crop(dirty_bbox)
                    pixel_bytes = pil_to_rgb565_bytes(region_to_send.convert("RGB"))
                    lcd.set_window(dirty_bbox[0], dirty_bbox[1], dirty_bbox[2] - 1, dirty_bbox[3] - 1)
                    lcd.write_pixels(pixel_bytes)

                elapsed_time = time.time() - frame_start_time
                sleep_duration = target_duration - elapsed_time
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

    except KeyboardInterrupt:
        log.info("\n終了しました。")
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        exit(1)
