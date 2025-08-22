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

from ..disp.st7789v import ST7789V
from ..utils.my_logger import get_logger
from ..utils.utils import (
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
    def __init__(self, x, y, radius, speed, angle, fill_color):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.speed_x = speed * np.cos(angle)
        self.speed_y = speed * np.sin(angle)
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
        return (int(self.x - self.radius), int(self.y - self.radius),
                int(self.x + self.radius), int(self.y + self.radius))

    def draw(self, image_buffer):
        """指定されたPIL Imageバッファにボールを描画する。"""
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
    speed = ball_speed or 300.0
    max_attempts_per_ball = 100  # 1つのボールを配置するための最大試行回数

    for _ in range(num_balls):
        for attempt in range(max_attempts_per_ball):
            # 新しいボールの候補を生成
            x = np.random.randint(BALL_RADIUS, width - BALL_RADIUS)
            y = np.random.randint(BALL_RADIUS, height - BALL_RADIUS)
            
            # 他のボールとの重なりをチェック
            is_overlapping = False
            for existing_ball in balls:
                dist_x = x - existing_ball.x
                dist_y = y - existing_ball.y
                dist_sq = dist_x**2 + dist_y**2
                # 半径の合計の2乗より小さい場合は重なっている
                if dist_sq <= (BALL_RADIUS + existing_ball.radius)**2:
                    is_overlapping = True
                    break
            
            # 重なっていなければ、この位置でボールを生成して次のボールへ
            if not is_overlapping:
                angle = np.random.rand() * 2 * np.pi
                fill_color = tuple(np.random.randint(0, 256, 3))
                balls.append(Ball(x, y, BALL_RADIUS, speed, angle, fill_color))
                break
        else:
            # forループがbreakで抜けなかった場合 (最大試行回数を超えた)
            log.warning(f"ボール{len(balls)+1}を配置できませんでした。ボールの数を減らすか、画面を大きくしてください。")

    return balls

def _handle_ball_collisions(balls: List[Ball]):
    """ボール同士の衝突を検出し、物理的に正しい反射を処理する。"""
    num_balls = len(balls)
    # 1回のパスで衝突を解決する。
    # 複数のボールが同時に衝突する状況を安定させるため、メインループ側で
    # 物理更新のサブステップ(num_physics_substeps)が実行される。
    for i in range(num_balls):
        for j in range(i + 1, num_balls):
            b1 = balls[i]
            b2 = balls[j]

            dist_x = b1.x - b2.x
            dist_y = b1.y - b2.y
            dist_sq = dist_x**2 + dist_y**2
            
            radii_sum = b1.radius + b2.radius
            radii_sum_sq = radii_sum**2

            # dist_sqが極端に小さい場合(ほぼ中心が同じ)は計算が不安定になるため除外
            if dist_sq <= radii_sum_sq and dist_sq > 1e-6:
                dist = np.sqrt(dist_sq)
                nx = dist_x / dist
                ny = dist_y / dist

                # 衝突軸上の相対速度を計算 (v1 - v2).
                # 法線ベクトルnはb2からb1を指す。内積が負の場合、接近している。
                relative_velocity_x = b1.speed_x - b2.speed_x
                relative_velocity_y = b1.speed_y - b2.speed_y
                relative_velocity_n = relative_velocity_x * nx + relative_velocity_y * ny

                # ボールが近づいている場合のみ速度を更新
                if relative_velocity_n < 0:
                    # 1. 衝突応答 (速度の更新)
                    # 接線ベクトル
                    tx = -ny
                    ty = nx

                    # 速度を n, t 成分に分解
                    v1n = b1.speed_x * nx + b1.speed_y * ny
                    v1t = b1.speed_x * tx + b1.speed_y * ty
                    v2n = b2.speed_x * nx + b2.speed_y * ny
                    v2t = b2.speed_x * tx + b2.speed_y * ty

                    # n 成分の速度を交換 (質量が等しい場合)
                    b1.speed_x = v2n * nx + v1t * tx
                    b1.speed_y = v2n * ny + v1t * ty
                    b2.speed_x = v1n * nx + v2t * tx
                    b2.speed_y = v1n * ny + v2t * ty

                # 2. 重なりの補正 (常に実行して、めり込みを解消)
                # 補正を強くして、1回の処理でほぼ解消するようにする
                correction_percent = 0.8  # 80%
                correction_slop = 0.01 # 許容するめり込み
                overlap = max(0, (radii_sum - dist + correction_slop))
                
                correction_amount = (overlap / 2) * correction_percent
                b1.x += correction_amount * nx
                b1.y += correction_amount * ny
                b2.x -= correction_amount * nx
                b2.y -= correction_amount * ny

def _main_loop(lcd: ST7789V, background: Image.Image, balls: List[Ball], 
               fps_counter: FpsCounter, font: ImageFont.ImageFont, target_fps: float):
    target_duration = 1.0 / target_fps
    next_frame_time = time.time()
    
    # --- 物理ステップの細分化 ---
    num_physics_substeps = 4
    sub_delta_t = target_duration / num_physics_substeps

    hud_layer = Image.new("RGBA", (lcd.width, lcd.height), (0, 0, 0, 0))
    hud_draw = ImageDraw.Draw(hud_layer)
    prev_fps_bbox = None

    while True:
        # --- 物理更新ループ ---
        for _ in range(num_physics_substeps):
            for ball in balls:
                # 壁との衝突判定は update_position 内で行われる
                ball.update_position(sub_delta_t, lcd.width, lcd.height)
            
            # ボール同士の衝突判定
            _handle_ball_collisions(balls)
        # -----------------------

        new_frame_image = background.copy()
        dirty_regions = []

        # 描画とダーティリージョンの計算
        for ball in balls:
            prev_bbox = ball.prev_bbox
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

        # フレームレートを維持するためのスリープ
        next_frame_time += target_duration
        sleep_duration = next_frame_time - time.time()
        if sleep_duration > 0:
            time.sleep(sleep_duration)

# --- CLIコマンド ---
@click.command("ball_anime")
@click.option('--spihz', "-z", default=SPI_SPEED_HZ, type=int, help='SPI speed in Hz', show_default=True)
@click.option('--fps', "-f", default=TARGET_FPS, type=float, help='Target frames per second', show_default=True)
@click.option('--num-balls', "-n", default=3, type=int, help='Number of balls to display', show_default=True)
@click.option('--ball-speed', "-b", default=None, type=float, help='Absolute speed of balls (pixels/second).')
def ball_anime(spihz: int, fps: float, num_balls: int, ball_speed: float):
    """物理ベースのアニメーションデモを実行する。"""
    log.info(f"最適化モードでフレームレート約{fps}FPSで動作します... Ctrl+C で終了してください。")

    try:
        with ST7789V(speed_hz=spihz) as lcd:
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
