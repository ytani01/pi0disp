#
# (c) 2025 Yoichi Tanibayashi
#
"""
pi0dispライブラリの基本的な使用方法を示すサンプルスクリプトです。
"""
import time
from pi0disp import ST7789V
from PIL import Image, ImageDraw

# --- 基本的な使用例 ---
print("基本的な使用例: 青い円を描画します。")

# ディスプレイを初期化
with ST7789V() as lcd:
    # PILを使って画像を作成
    image = Image.new("RGB", (lcd.width, lcd.height), "black")
    draw = ImageDraw.Draw(image)

    # 円を描画
    draw.ellipse(
        (10, 10, lcd.width - 10, lcd.height - 10),
        fill="blue",
        outline="white"
    )

    # ディスプレイに表示
    lcd.display(image)

    print("5秒間表示します...")
    time.sleep(5)

    # --- 部分更新（差分描画）の例 ---
    print("部分更新の例: 中央に赤い四角を追加します。")

    # 画像の一部を変更
    draw.rectangle((50, 50, 100, 100), fill="red")

    # 変更された領域のみをディスプレイに転送
    lcd.display_region(image, 50, 50, 100, 100)

    print("5秒間表示します...")
    time.sleep(5)

print("サンプルプログラムを終了します。")
