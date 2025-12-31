#!/usr/bin/env python3
#
# (c) 2025 Yoichi Tanibayashi
#
"""
Simple Drawing Sample for ST7789V
図形、テキスト、複数の色を使用した基本的な描画サンプル。
"""

import os
import time

from PIL import Image, ImageDraw, ImageFont

from pi0disp.disp.st7789v import ST7789V


def main():
    # 1. ディスプレイの初期化 (横向き)
    disp = ST7789V(rotation=90)
    width, height = disp.size.width, disp.size.height

    # 2. 描画用キャンバスの作成 (黒背景)
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    # 3. 図形の描画
    # 四角形 (黄色い枠)
    draw.rectangle([20, 20, 120, 120], outline="yellow", width=3)

    # 円 (赤い塗りつぶし)
    draw.ellipse([180, 30, 280, 130], fill="red", outline="white")

    # 直線 (緑)
    draw.line([0, height - 1, width - 1, 0], fill="green", width=2)

    # 4. テキストの描画
    # フォントの読み込み (システムフォントを優先)
    font_path = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
    if os.path.exists(font_path):
        font = ImageFont.truetype(font_path, 40)
    else:
        font = ImageFont.load_default()

    # 中央付近に文字を表示
    text = "pi0disp"
    draw.text((80, 150), text, fill="cyan", font=font)

    # 5. ディスプレイに表示
    disp.display(img)

    # 6. 5秒間表示を維持 (キー入力待ちの代わりに sleep を使用)
    print("Displaying for 5 seconds...")
    time.sleep(5)

    # 7. 終了処理
    disp.close()


if __name__ == "__main__":
    main()
