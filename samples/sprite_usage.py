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
sys.path.append(str(
    Path(__file__).parent.parent
))

from pi0disp.disp.st7789v import ST7789V
from pi0disp.utils.sprite import Sprite
from pi0disp.utils.performance_core import RegionOptimizer
from pi0disp.utils.utils import expand_bbox

# --- Configuration ---
NUM_BALLS = 5
BALL_RADIUS = 15
TARGET_FPS = 30

class Ball(Sprite):
    """
    Spriteクラスを継承した、跳ね返るボールのスプライト。
    Spriteクラスを継承することで、
    位置、サイズ、ダーティリージョン管理の恩恵を受けます。
    抽象メソッドである `update` と `draw` を
    実装する必要があります。
    """
    def __init__(self, x, y, radius, speed_x,
                 speed_y, color, screen_width, screen_height):
        # Spriteクラスのコンストラクタを呼び出し、
        # スプライトの初期位置とサイズを設定します。
        # Spriteは矩形として扱われるため、
        # 幅と高さは直径(radius * 2)になります。
        super().__init__(x, y, radius * 2, radius * 2)
        self.radius = radius
        self.speed_x = speed_x
        self.speed_y = speed_y
        self.color = color
        self.screen_width = screen_width
        self.screen_height = screen_height

    def update(self, delta_t: float):
        """
        Spriteクラスの抽象メソッドを実装します。
        ボールの位置を更新し、画面の境界で反射させます。
        `delta_t` (前回のフレームからの経過時間) を使用して、
        動きをフレームレートに依存させないようにします。
        """
        self.x += self.speed_x * delta_t
        self.y += self.speed_y * delta_t

        # 画面の境界での反射処理
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
        """
        Spriteクラスの抽象メソッドを実装します。
        指定されたPIL ImageDrawオブジェクトにボールを描画します。
        `self.bbox` はSpriteクラスから提供される
        現在のバウンディングボックスです。
        """
        draw.ellipse(self.bbox, fill=self.color)

def main():
    """メイン関数"""
    with ST7789V() as lcd:
        width, height = lcd.width, lcd.height

        # ディスプレイ全体を黒で初期化します。
        # これにより、アニメーション開始時の残像を防ぎます。
        image = Image.new("RGB", (width, height), "black")
        lcd.display(image)  # 画面をクリア

        # ボール（スプライト）を初期化
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
                    speed_x=(random.uniform(50, 150) *
                             random.choice([-1, 1])),
                    speed_y=(random.uniform(50, 150) *
                             random.choice([-1, 1])),
                    color=color,
                    screen_width=width,
                    screen_height=height
                )
            )

        # メインループ
        target_duration = 1.0 / TARGET_FPS
        last_time = time.time()

        print("アニメーションを開始します... Ctrl+Cで終了")
        while True:
            current_time = time.time()
            delta_t = current_time - last_time
            last_time = current_time

            dirty_regions = []

            # 各スプライトの状態を更新し、前後の位置から
            # ダーティリージョンを収集します。
            # `s.get_dirty_region()` は前回の描画領域と
            # 現在の描画領域を結合したものです。
            for s in sprites:
                s.update(delta_t)
                dirty_regions.append(s.get_dirty_region())

            # 収集したダーティリージョンを最適化（結合）し、
            # 更新領域の数を減らします。
            # RegionOptimizer.merge_regionsは、重複または近接する矩形領域を
            # 結合して、描画操作の数を減らすために使用されます。
            # `max_regions` は結合後の最大領域数です。
            optimized_regions = RegionOptimizer.merge_regions(
                [r for r in dirty_regions if r],
                max_regions=8
            )

            # 描画処理
            draw = ImageDraw.Draw(image)
            # 最適化されたダーティリージョンを黒でクリアします。
            # PILのアンチエイリアシングによるピクセルの漏れ出しを防ぐため、
            # `expand_bbox` で領域を1ピクセル拡大しています。
            # expand_bboxは、バウンディングボックスを全方向に指定された
            # ピクセル数だけ拡大します。
            for r in optimized_regions:
                expanded_r = expand_bbox(r, 1)  # 1ピクセル拡大
                draw.rectangle(expanded_r, fill="black")
            
            # 各スプライトを現在の位置に描画し、
            # 次フレームのダーティリージョン計算のために
            # 現在のバウンディングボックスを記録します。
            for s in sprites:
                s.draw(draw)
                s.record_current_bbox()

            # 更新が必要な領域のみをディスプレイに転送します。
            # ここでも`expand_bbox`で領域を拡大し、
            # `clamp_region`で画面内に収めます。
            # RegionOptimizer.clamp_regionは、領域の座標を画面の境界内に
            # 収まるように調整します。
            for r in optimized_regions:
                expanded_r = expand_bbox(r, 1)  # 1ピクセル拡大
                clamped_r = RegionOptimizer.clamp_region(
                    expanded_r, width, height
                )
                if (clamped_r[2] > clamped_r[0] and
                        clamped_r[3] > clamped_r[1]):
                    lcd.display_region(image, *clamped_r)

            # 目標フレームレートを維持するために、必要に応じてスリープします。
            sleep_duration = target_duration - \
                             (time.time() - current_time)
            if sleep_duration > 0:
                time.sleep(sleep_duration)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n終了しました。")
