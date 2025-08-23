#
# (c) 2025 Yoichi Tanibayashi
#
"""
Spriteクラスの使用方法を示すサンプルスクリプトです。
複数のボールが画面内で跳ね返るアニメーションを表示します。
"""
import time
import sys
from pathlib import Path
import random
import colorsys
from typing import List

from PIL import Image, ImageDraw

# Add project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from pi0disp.disp.st7789v import ST7789V
from pi0disp.utils.sprite import Sprite
from pi0disp.utils.performance_core import RegionOptimizer
from pi0disp.utils.utils import expand_bbox

# --- Configuration ---
NUM_BALLS = 5
BALL_RADIUS = 15
TARGET_FPS = 30

class Ball(Sprite):
    """跳ね返るボールのスプライト。"""
    def __init__(self, x, y, radius, speed_x, speed_y, color, screen_width, screen_height):
        super().__init__(x, y, radius * 2, radius * 2)
        self.radius = radius
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height

    def update(self, delta_t: float):
        """ボールの位置を更新し、画面の境界で反射させます。"""
        self.x += self.speed_x * delta_t
        self.y += self.speed_y * delta_t

        if self.x < 0:
            self.x = 0
            self.speed_x = -self.speed_x
        if self.x + self.width > self.screen_width:
            self.x = self.screen_width - self.width
            self.speed_x = -self.speed_x
        if self.y < 0:
            self.y = 0
            self.speed_y = -self.speed_y
        if self.y + self.height > self.screen_height:
            self.y = self.screen_height - self.height
            self.speed_y = -self.speed_y

    def draw(self, draw: ImageDraw.ImageDraw):
        """ボールを描画します。"""
        draw.ellipse(self.bbox, fill=self.color)

def main():
    """メイン関数"""
    with ST7789V() as lcd:
        width, height = lcd.width, lcd.height

        # ボールを初期化
        sprites: List[Sprite] = []
        hues = [i / NUM_BALLS for i in range(NUM_BALLS)]
        for i in range(NUM_BALLS):
            rgb_float = colorsys.hsv_to_rgb(hues[i], 1.0, 1.0)
            color = tuple(int(c * 255) for c in rgb_float)
            
            sprites.append(
                Ball(
                    x=random.uniform(0, width - BALL_RADIUS * 2),
                    y=random.uniform(0, height - BALL_RADIUS * 2),
                    radius=BALL_RADIUS,
                    speed_x=random.uniform(50, 150) * random.choice([-1, 1]),
                    speed_y=random.uniform(50, 150) * random.choice([-1, 1]),
                    color=color,
                    screen_width=width,
                    screen_height=height
                )
            )

        # メインループ
        target_duration = 1.0 / TARGET_FPS
        last_time = time.time()
        start_time = last_time
        screenshot_saved = False

        image = Image.new("RGB", (width, height), "black")
        lcd.display(image) # 画面をクリア

        print("アニメーションを開始します... Ctrl+Cで終了")
        while True:
            current_time = time.time()
            delta_t = current_time - last_time
            last_time = current_time

            # 5秒後にスクリーンショットを撮影
            if not screenshot_saved and (current_time - start_time) >= 2.0:
                print("スクリーンショットを screenshot.png に保存します...")
                image.save("screenshot.png")
                screenshot_saved = True
                # sys.exit() # スクリーンショット後に終了しないようにコメントアウト

            dirty_regions = []

            # スプライトの状態を更新し、ダーティリージョンを収集
            for s in sprites:
                s.update(delta_t)
                dirty_regions.append(s.get_dirty_region())

            # ダーティリージョンを最適化
            optimized_regions = RegionOptimizer.merge_regions(
                [r for r in dirty_regions if r], max_regions=8
            )

            # 描画
            draw = ImageDraw.Draw(image)
            # ダーティリージョンをクリア
            for r in optimized_regions:
                expanded_r = expand_bbox(r, 1) # 1ピクセル拡大
                draw.rectangle(expanded_r, fill="black")
            
            # スプライトを描画し、バウンディングボックスを記録
            for s in sprites:
                s.draw(draw)
                s.record_current_bbox()

            # ディスプレイに転送
            for r in optimized_regions:
                expanded_r = expand_bbox(r, 1) # 1ピクセル拡大
                clamped_r = RegionOptimizer.clamp_region(expanded_r, width, height)
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
