#
# (c) 2025 Yoichi Tanibayashi
#
"""
Spriteクラスを使用してロボットの顔アニメーションを実装するサンプルです。
状態管理と描画がSpriteクラスにカプセル化されています。
"""
import time
import sys
from pathlib import Path
from typing import Tuple, List
import math

from PIL import Image, ImageDraw, ImageFont

# Add project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from pi0disp.disp.st7789v import ST7789V
from pi0disp.utils.sprite import Sprite
from pi0disp.utils.performance_core import RegionOptimizer

# --- Configuration ---
TARGET_FPS = 15
BACKGROUND_COLOR = (0, 0, 0)
FACE_COLOR = (255, 255, 255)
FONT_PATH = "../src/pi0disp/fonts/Firge-Regular.ttf"

class RobotFace(Sprite):
    """Spriteを継承したロボットの顔クラス。"""

    def __init__(self, x: int, y: int, width: int, height: int):
        super().__init__(x, y, width, height)
        self.expressions = ["neutral", "happy", "sad", "blinking"]
        self.current_expression_index = 0
        self.expression_timer = 0
        self.expression_duration = 2.0  # 各表情の表示時間（秒）
        self.blink_state_timer = 0
        self.is_blinking_closed = False

        # 顔のパーツのジオメトリを計算
        self.eye_radius = int(width * 0.15)
        self.eye_y = y + int(height * 0.4)
        self.left_eye_x = x + int(width * 0.3)
        self.right_eye_x = x + int(width * 0.7)
        self.mouth_y = y + int(height * 0.75)
        self.mouth_rect = (
            x + int(width * 0.25), self.mouth_y,
            x + int(width * 0.75), self.mouth_y + int(height * 0.15)
        )

    def update(self, delta_t: float):
        """表情の状態を時間に基づいて更新します。"""
        self.expression_timer += delta_t
        if self.expression_timer > self.expression_duration:
            self.expression_timer = 0
            self.current_expression_index = (self.current_expression_index + 1) % len(self.expressions)

        if self.expressions[self.current_expression_index] == "blinking":
            self.blink_state_timer += delta_t
            if self.blink_state_timer > 0.15: # まばたきの速度
                self.blink_state_timer = 0
                self.is_blinking_closed = not self.is_blinking_closed

    def draw(self, draw: ImageDraw.ImageDraw):
        """現在の表情に基づいて顔を描画します。"""
        expression = self.expressions[self.current_expression_index]

        # --- 目を描画 ---
        if expression == "blinking":
            if self.is_blinking_closed:
                self._draw_closed_eye(draw, self.left_eye_x)
                self._draw_closed_eye(draw, self.right_eye_x)
            else:
                self._draw_open_eye(draw, self.left_eye_x)
                self._draw_open_eye(draw, self.right_eye_x)
        elif expression == "happy":
            self._draw_happy_eye(draw, self.left_eye_x)
            self._draw_happy_eye(draw, self.right_eye_x)
        else: # neutral, sad
            self._draw_open_eye(draw, self.left_eye_x)
            self._draw_open_eye(draw, self.right_eye_x)

        # --- 口を描画 ---
        if expression == "happy":
            draw.arc(self.mouth_rect, 0, 180, fill=FACE_COLOR, width=4)
        elif expression == "sad":
            draw.arc(self.mouth_rect, 180, 360, fill=FACE_COLOR, width=4)
        else: # neutral, blinking
            draw.line((self.mouth_rect[0], self.mouth_y, self.mouth_rect[2], self.mouth_y), fill=FACE_COLOR, width=4)

    def _draw_open_eye(self, draw: ImageDraw.ImageDraw, center_x: int):
        bbox = (center_x - self.eye_radius, self.eye_y - self.eye_radius,
                center_x + self.eye_radius, self.eye_y + self.eye_radius)
        draw.ellipse(bbox, outline=FACE_COLOR, width=2)

    def _draw_closed_eye(self, draw: ImageDraw.ImageDraw, center_x: int):
        draw.line((center_x - self.eye_radius, self.eye_y,
                   center_x + self.eye_radius, self.eye_y), fill=FACE_COLOR, width=2)

    def _draw_happy_eye(self, draw: ImageDraw.ImageDraw, center_x: int):
        bbox = (center_x - self.eye_radius, self.eye_y - self.eye_radius,
                center_x + self.eye_radius, self.eye_y + self.eye_radius)
        draw.arc(bbox, 180, 360, fill=FACE_COLOR, width=3)


def main():
    """メイン関数"""
    with ST7789V() as lcd:
        width, height = lcd.width, lcd.height
        image = Image.new("RGB", (width, height), BACKGROUND_COLOR)
        draw = ImageDraw.Draw(image)

        # RobotFaceスプライトを作成
        face = RobotFace(0, 0, width, height)
        sprites: List[Sprite] = [face]

        # メインループ
        target_duration = 1.0 / TARGET_FPS
        last_time = time.time()

        print("アニメーションを開始します... Ctrl+Cで終了")
        while True:
            current_time = time.time()
            delta_t = current_time - last_time
            last_time = current_time

            dirty_regions = []

            # スプライトの状態を更新し、ダーティリージョンを収集
            for s in sprites:
                s.update(delta_t)
                dirty_regions.append(s.get_dirty_region())

            # ダーティリージョンを最適化
            optimized_regions = RegionOptimizer.merge_regions(
                [r for r in dirty_regions if r], max_regions=4
            )

            # ダーティリージョンをクリア
            for r in optimized_regions:
                draw.rectangle(r, fill=BACKGROUND_COLOR)
            
            # スプライトを描画し、バウンディングボックスを記録
            for s in sprites:
                s.draw(draw)
                s.record_current_bbox()

            # ディスプレイに転送
            for r in optimized_regions:
                clamped_r = RegionOptimizer.clamp_region(r, width, height)
                if clamped_r[2] > clamped_r[0] and clamped_r[3] > clamped_r[1]:
                    lcd.display_region(image, *clamped_r)

            # フレームレートを維持
            sleep_duration = target_duration - (time.time() - current_time)
            if sleep_duration > 0:
                time.sleep(sleep_duration)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n終了しました。")
