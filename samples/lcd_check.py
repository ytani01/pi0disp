import time
from typing import Union

from PIL import Image, ImageDraw, ImageFont

from pi0disp import ST7789V

# 1. ディスプレイの初期化
# デフォルト設定 (invert=True, bgr=True) で初期化
# 実際のピン番号に合わせてSpiPinsを設定してください
# 例: pin = SpiPins(rst=25, dc=24, bl=23)
# size = DispSize(width=240, height=320)
try:
    with ST7789V(
        # pin=SpiPins(rst=25, dc=24, bl=23), # 必要に応じてコメントを外して設定
        # size=DispSize(width=240, height=320), # 必要に応じてコメントを外して設定
        invert=True,
        bgr=True,
        debug=False,
    ) as lcd:
        print("ディスプレイ初期化完了")

        # 2. 赤い画面を表示
        print("赤い画面を表示します (5秒間)")
        red_image = Image.new("RGB", lcd.size, "red")
        lcd.display(red_image)
        time.sleep(5)

        # --- 回転の視認性改善 ---
        # 3. 回転テスト
        print("回転テストを開始します。checkerboardパターンとTOP表示")

        # 回転テスト用の画像を作成
        # checkerboardパターン
        check_size = 20
        check_color1 = (255, 0, 0)  # 赤
        check_color2 = (0, 0, 255)  # 青
        base_image = Image.new(
            "RGB", (lcd.native_size.width, lcd.native_size.height), "white"
        )
        draw = ImageDraw.Draw(base_image)
        for y in range(0, lcd.native_size.height, check_size):
            for x in range(0, lcd.native_size.width, check_size):
                if (x // check_size + y // check_size) % 2 == 0:
                    draw.rectangle(
                        [x, y, x + check_size, y + check_size],
                        fill=check_color1,
                    )
                else:
                    draw.rectangle(
                        [x, y, x + check_size, y + check_size],
                        fill=check_color2,
                    )

        # "TOP"ラベルを追加
        font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]
        try:
            # Load a font (adjust path as needed, or use a default pillow font)
            font_size = 30
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except IOError:
            # Fallback to a simpler font if DejavuSans-Bold.ttf is not found
            font = ImageFont.load_default()
            font_size = 15  # Smaller font size for default font

        text = "TOP"
        text_bbox = draw.textbbox((0, 0), text, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]
        text_x = (lcd.native_size.width - text_width) // 2
        text_y = (lcd.native_size.height - text_height) // 2
        draw.text(
            (text_x, text_y), text, fill=(255, 255, 255), font=font
        )  # 白文字

        rotations = [0, 90, 180, 270]
        for rot in rotations:
            print(f"回転: {rot}度 (5秒間)")
            lcd.set_rotation(rot)
            lcd.display(base_image)  # 同じ画像を再表示
            time.sleep(5)

        # 回転テスト後、一度バックライトを元に戻すためにデフォルト設定で再表示
        print("回転テスト終了。デフォルト設定に戻します。")
        lcd.set_rotation(0)  # 0度に戻す
        lcd.display(
            Image.new("RGB", lcd.size, "green")
        )  # 緑の画面に戻す (元の3.の動作)
        time.sleep(2)
        # --- 回転の視認性改善 終了 ---

        # 4. 青い画面を表示し、バックライトを制御
        print("青い画面を表示し、バックライトを50%に設定します (5秒間)")
        blue_image = Image.new("RGB", lcd.size, "blue")
        lcd.set_rotation(0)  # 回転を元に戻す
        lcd.set_brightness(128)  # バックライトを50%の明るさに
        lcd.display(blue_image)
        time.sleep(5)
        lcd.set_brightness(255)  # バックライトを元の明るさに戻す

        # 5. invert=False (反転なし) でテスト
        # 一旦閉じて、新しい設定で再初期化
        lcd.close()  # 既存のLCDインスタンスを閉じる
        with ST7789V(invert=False, bgr=True) as lcd_no_invert:
            print("反転なしで赤い画面を表示します (5秒間)")
            red_image_no_invert = Image.new("RGB", lcd_no_invert.size, "red")
            lcd_no_invert.display(red_image_no_invert)
            time.sleep(5)

        # 6. bgr=False (RGB順) でテスト
        # 一旦閉じて、新しい設定で再初期化
        # lcd_no_invert.close() # 既に閉じてるので不要
        with ST7789V(invert=True, bgr=False) as lcd_rgb_order:
            print("RGB順で赤い画面を表示します (5秒間)")
            red_image_rgb_order = Image.new("RGB", lcd_rgb_order.size, "red")
            lcd_rgb_order.display(red_image_rgb_order)
            time.sleep(5)

        print("テスト終了。")

except RuntimeError as e:
    print(f"エラー: {e}")
except KeyboardInterrupt:
    print("スクリプトがユーザーによって中断されました。")
