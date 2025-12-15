#
# (c) 2025 Yoichi Tanibayashi
#
"""
pi0dispライブラリの基本的な使用方法を示すサンプルスクリプトです。
"""

import time

from PIL import Image, ImageDraw

from pi0disp import ST7789V

# --- 基本的な使用例 ---
print("基本的な使用例: 青い円を描画します。")

# ディスプレイを初期化
with ST7789V(debug=True) as lcd:
    # PILを使って画像を作成
    image1 = Image.new("RGB", (lcd.width, lcd.height), "white")
    # image2 = image1.copy()
    draw = ImageDraw.Draw(image1)
    lcd.display(image1)

    draw = ImageDraw.Draw(image1)

    time.sleep(2)

    # 円を描画
    draw.ellipse(
        (10, 10, lcd.width - 10, lcd.height - 10),
        fill="blue",
        outline="white",
    )

    # ディスプレイに表示
    lcd.display(image1)

    draw = ImageDraw.Draw(image1)
    time.sleep(2)

    # --- 部分更新（差分描画）の例 ---
    print("部分更新の例: 中央に赤い四角を追加します。")

    # 画像の一部を変更
    W: int = 100
    H: int = 50

    x1: int = int(lcd.width / 2 - W / 2)
    y1: int = int(lcd.height / 2 - H / 2)
    x2: int = x1 + W
    y2: int = y1 + H

    draw.rectangle((x1, y1, x2, y2), fill="red")

    # 変更された領域のみをディスプレイに転送
    lcd.display_region(image1, x1, y1, x2, y2)

    time.sleep(1)

print("サンプルプログラムを終了します。")
