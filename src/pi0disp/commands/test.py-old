# -*- coding: utf-8 -*-
"""
ST7789Vディスプレイで動作する、物理ベースのアニメーションデモ。

このスクリプトは、シンプルなボールのアニメーションを通じて、
組込み環境やシングルボードコンピュータで滑らかなグラフィックスを
実現するための、以下の主要なテクニックを実装しています。

1.  **numpyによる高速ピクセル変換:**
    PILのImageオブジェクトからLCD用のRGB565形式への変換を、
    numpyのベクトル化処理を用いて高速に実行します。

2.  **差分描画 (ダーティ矩形):**
    毎フレーム画面全体を更新するのではなく、ボールの移動によって変化が
    あった領域（ダーティ矩形）だけを特定し、その最小限の範囲のみを
    LCDに転送することで、データ転送量を劇的に削減します。

3.  **デルタタイムによる物理更新:**
    アニメーションの速度をフレームレートから独立させます。
    これにより、処理負荷が変動しても、ボールは常に人間が見て
    一定の速度で動くようになります。

4.  **フレームレート制限 (FPS Capping):**
    CPUリソースを100%使い切るのを防ぎ、指定したフレームレート
    （例: 30 FPS）を維持するように意図的に待機時間を挿入します。
    これにより、システムの負荷を軽減し、安定した動作を実現します。
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
    """アニメーションの挙動を調整するための設定値"""
    # ディスプレイ設定
    SPI_SPEED_HZ = 16000000  # SPIクロック周波数

    # パフォーマンス設定
    TARGET_FPS = 30.0  # 目標フレームレート

    # ボールの物理設定
    BALL_RADIUS = 20
    BALL_INITIAL_SPEED_X = 300.0  # 横方向の速度 (ピクセル/秒)
    BALL_INITIAL_SPEED_Y = 200.0  # 縦方向の速度 (ピクセル/秒)

    # 描画設定
    BALL_FILL_COLOR = (255, 255, 0)
    BALL_OUTLINE_COLOR = (255, 255, 255)
    
    # FPSカウンター設定
    FPS_FONT_PATH = "Firge-Regular.ttf"
    FPS_FONT_SIZE = 50
    FPS_TEXT_COLOR = (255, 255, 255)
    FPS_UPDATE_INTERVAL = 0.2  # FPS表示の更新間隔 (秒)
    FPS_AREA_PADDING = 5      # FPS表示領域の余白

# --- 描画オブジェクトクラス ---
class Ball:
    """ボールの状態と振る舞いを管理するクラス"""
    def __init__(self, x, y, radius, speed_x, speed_y, fill_color):
        self.x = float(x)
        self.y = float(y)
        self.radius = radius
        self.speed_x = float(speed_x)
        self.speed_y = float(speed_y)
        self.fill_color = fill_color
        self.prev_bbox = None

    def update_position(self, delta_t, screen_width, screen_height):
        """デルタタイムに基づいてボールの位置を更新し、壁での反射を処理する"""
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
        """現在のボールの位置からバウンディングボックスを計算する"""
        return (
            int(self.x - self.radius), int(self.y - self.radius),
            int(self.x + self.radius), int(self.y + self.radius)
        )

    def draw(self, image_buffer):
        """ボールをイメージバッファに描画し、更新領域を返す"""
        curr_bbox = self.get_bbox()
        update_bbox = merge_bboxes(self.prev_bbox, curr_bbox)
        
        if update_bbox:
            # 安全マージンを追加
            update_bbox = (
                max(0, update_bbox[0] - 1), max(0, update_bbox[1] - 1),
                min(image_buffer.width, update_bbox[2] + 1), min(image_buffer.height, update_bbox[3] + 1),
            )
            
            # ボールを描画するImageオブジェクトを作成 (RGBモード)
            ball_image = Image.new("RGB", (self.radius * 2, self.radius * 2), self.fill_color)
            
            # ボールの形状を表すアルファマスクを作成
            mask = Image.new("L", (self.radius * 2, self.radius * 2), 0) # Lモード (8-bit pixels, black and white)
            draw_mask = ImageDraw.Draw(mask)
            draw_mask.ellipse((0, 0, self.radius * 2, self.radius * 2), fill=255) # 円形部分を白 (不透明) に

            # image_buffer にボールをマスクを使って貼り付け
            paste_x = curr_bbox[0]
            paste_y = curr_bbox[1]
            image_buffer.paste(ball_image, (paste_x, paste_y), mask)
            
            self.prev_bbox = curr_bbox
            return update_bbox
        
        self.prev_bbox = curr_bbox
        return None

class FpsCounter:
    """FPSの計算と描画を管理するクラス"""
    def __init__(self, lcd, initial_background_image):
        try:
            self.font = ImageFont.truetype(CONFIG.FPS_FONT_PATH, CONFIG.FPS_FONT_SIZE)
            log.info(f"'{CONFIG.FPS_FONT_PATH}' フォントを読み込みました。")
        except IOError:
            log.warning(f"警告: '{CONFIG.FPS_FONT_PATH}' が見つかりません。デフォルトフォントを使用します。")
            self.font = ImageFont.load_default()

        # 文字欠けを防ぐため、textbboxのオフセットを考慮した固定描画領域を計算
        padding = CONFIG.FPS_AREA_PADDING
        pos = (padding, padding)
        base_bbox = ImageDraw.Draw(initial_background_image).textbbox((0,0), "FPS: 999", font=self.font)
        box_width = base_bbox[2] - base_bbox[0] + (padding * 2)
        box_height = base_bbox[3] - base_bbox[1] + (padding * 2)
        
        self.bbox = (pos[0], pos[1], pos[0] + box_width, pos[1] + box_height)
        self.draw_offset = (padding - base_bbox[0], padding - base_bbox[1])

        self.frame_count = 0
        self.last_update_time = time.time()
        self.initial_background_image = initial_background_image # 追加

    def update_and_draw(self, image_buffer):
        """FPSを計算し、更新タイミングであれば描画する"""
        self.frame_count += 1
        current_time = time.time()
        elapsed = current_time - self.last_update_time

        if elapsed >= CONFIG.FPS_UPDATE_INTERVAL:
            fps = self.frame_count / elapsed
            fps_text = f"FPS: {fps:.0f}"
            
            # 描画処理
            draw = ImageDraw.Draw(image_buffer)
            
            # FPSテキストを描画
            draw.text((self.bbox[0] + self.draw_offset[0], self.bbox[1] + self.draw_offset[1]), 
                      fps_text, font=self.font, fill=CONFIG.FPS_TEXT_COLOR)
            
            # カウンタをリセット
            self.frame_count = 0
            self.last_update_time = current_time
            
            return self.bbox
        
        return None

@click.command()
@click.option('--speed', default=CONFIG.SPI_SPEED_HZ, type=int, help='SPI speed in Hz', show_default=True)
@click.option('--fps', default=CONFIG.TARGET_FPS, type=float, help='Target frames per second', show_default=True)
@click.option('--num-balls', default=3, type=int, help='Number of balls to display', show_default=True)
@click.option('--ball-speed', default=None, type=float, help='Absolute speed of balls (pixels/second). If not specified, balls will have random speeds based on internal configuration.')
def test(speed, fps, num_balls, ball_speed):
    """
    Run the physics-based animation demo (test3).
    """
    CONFIG.SPI_SPEED_HZ = speed
    CONFIG.TARGET_FPS = fps

    log.info(f"フレームレートを約{CONFIG.TARGET_FPS}FPSに制限します... Ctrl+C で終了してください。")

    try:
        with ST7789V(speed_hz=CONFIG.SPI_SPEED_HZ) as lcd:
            # 1. 初期背景画像を生成
            initial_background_image = Image.new("RGB", (lcd.width, lcd.height))
            draw = ImageDraw.Draw(initial_background_image)
            for y in range(lcd.height):
                color = (y % 256, (y*2) % 256, (y*3) % 256)
                draw.line((0, y, lcd.width, y), fill=color)
            
            # 2. ソフトウェアフレームバッファを初期化し、背景を描画
            current_frame_image = initial_background_image.copy() # 初期背景でバッファを初期化
            lcd.display(current_frame_image) # 初回表示

            # 3. オブジェクトを初期化
            balls = []
            for i in range(num_balls):
                x = np.random.randint(CONFIG.BALL_RADIUS, lcd.width - CONFIG.BALL_RADIUS)
                y = np.random.randint(CONFIG.BALL_RADIUS, lcd.height - CONFIG.BALL_RADIUS)
                
                if ball_speed is not None:
                    # 指定された絶対速度に基づいて速度ベクトルを生成
                    angle = np.random.rand() * 2 * np.pi
                    speed_x = ball_speed * np.cos(angle)
                    speed_y = ball_speed * np.sin(angle)
                else:
                    # デフォルトの速度とランダムな変動を使用
                    speed_x = CONFIG.BALL_INITIAL_SPEED_X * (1 + (np.random.rand() - 0.5) * 0.5)
                    speed_y = CONFIG.BALL_INITIAL_SPEED_Y * (1 + (np.random.rand() - 0.5) * 0.5)

                fill_color = (np.random.randint(0, 256), np.random.randint(0, 256), np.random.randint(0, 256))
                balls.append(Ball(x, y, CONFIG.BALL_RADIUS, speed_x, speed_y, fill_color))

            fps_counter = FpsCounter(lcd, initial_background_image)
            
            # 4. メインループ
            last_frame_time = time.time()
            target_duration = 1.0 / CONFIG.TARGET_FPS

            while True:
                # --- 時間管理 ---
                frame_start_time = time.time()
                delta_t = frame_start_time - last_frame_time
                last_frame_time = frame_start_time

                # --- 更新と描画 ---
                # 新しいフレームの画像を初期背景で開始
                new_frame_image = initial_background_image.copy()
                
                # ダーティ領域を収集するためのリスト
                dirty_regions = []

                # ボールの位置を更新し、新しいフレームに描画
                for ball in balls:
                    # 描画前のprev_bboxを保存
                    prev_bbox_before_draw = ball.prev_bbox
                    ball.update_position(delta_t, lcd.width, lcd.height)
                    ball.draw(new_frame_image) # 新しいフレームバッファに描画
                    curr_bbox_after_draw = ball.get_bbox()
                    
                    # ダーティ領域を計算し、リストに追加
                    ball_dirty_bbox = merge_bboxes(prev_bbox_before_draw, curr_bbox_after_draw)
                    if ball_dirty_bbox:
                        # 安全マージンを追加
                        ball_dirty_bbox = (
                            max(0, ball_dirty_bbox[0] - 1), max(0, ball_dirty_bbox[1] - 1),
                            min(lcd.width, ball_dirty_bbox[2] + 1), min(lcd.height, ball_dirty_bbox[3] + 1),
                        )
                        dirty_regions.append(ball_dirty_bbox)

                # FPSカウンターを更新し、新しいフレームに描画
                fps_dirty_bbox = fps_counter.update_and_draw(new_frame_image)
                if fps_dirty_bbox:
                    # 安全マージンを追加
                    fps_dirty_bbox = (
                        max(0, fps_dirty_bbox[0] - 1), max(0, fps_dirty_bbox[1] - 1),
                        min(lcd.width, fps_dirty_bbox[2] + 1), min(lcd.height, fps_dirty_bbox[3] + 1),
                    )
                    dirty_regions.append(fps_dirty_bbox)

                # LCDにダーティ領域のみを転送
                for dirty_bbox in dirty_regions:
                    region_to_send = new_frame_image.crop(dirty_bbox)
                    pixel_bytes = pil_to_rgb565_bytes(region_to_send)
                    lcd.set_window(dirty_bbox[0], dirty_bbox[1], dirty_bbox[2] - 1, dirty_bbox[3] - 1)
                    lcd.write_pixels(pixel_bytes)
                
                # current_frame_image を新しいフレームの画像で更新 (次フレームの比較用)
                current_frame_image = new_frame_image.copy()
                # 処理にかかった時間に応じて待機時間を計算し、CPU負荷を軽減する
                elapsed_time = time.time() - frame_start_time
                sleep_duration = target_duration - elapsed_time
                if sleep_duration > 0:
                    time.sleep(sleep_duration)

    except KeyboardInterrupt:
        log.info("\n終了しました。" )
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        exit(1)

