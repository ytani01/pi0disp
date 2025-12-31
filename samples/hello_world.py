import time

from PIL import Image, ImageDraw

from pi0disp import ST7789V

# コンテキストマネージャによる自動 close()
with ST7789V(rotation=ST7789V.EAST, brightness=128) as lcd:
    # 現在の画面サイズに合わせたキャンバスを作成
    img = Image.new("RGB", lcd.size, "black")
    draw = ImageDraw.Draw(img)

    # 描画の例
    draw.rectangle(
        (0, 0, lcd.size.width - 1, lcd.size.height - 1), outline="white"
    )
    draw.text((20, 20), "ST7789V Reference", fill="yellow")

    # 画面に転送
    lcd.display(img)

    time.sleep(10)
