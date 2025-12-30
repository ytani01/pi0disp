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
        bgr=True,  # BGRカラー順序をテスト
        debug=False,
    ) as lcd:
        print("ディスプレイ初期化完了")
        print(f"ディスプレイサイズ: {lcd.size.width}x{lcd.size.height}")

        colors = {
            "Red": (255, 0, 0),
            "Green": (0, 255, 0),
            "Blue": (0, 0, 255),
            "White": (255, 255, 255),
            "Black": (0, 0, 0),
        }

        # フォントの準備
        font: Union[ImageFont.FreeTypeFont, ImageFont.ImageFont]
        try:
            font_size = 20
            # フォントファイルが見つからない場合は、適切なパスに修正するか、デフォルトフォントを使用
            font = ImageFont.truetype("DejaVuSans-Bold.ttf", font_size)
        except IOError:
            print(
                "DejaVuSans-Bold.ttf が見つかりません。デフォルトフォントを使用します。"
            )
            font = ImageFont.load_default()
            font_size = 15

        for name, color in colors.items():
            print(f"{name} の画面を表示します (3秒間)")
            # 全画面を単色で塗りつぶす
            solid_image = Image.new("RGB", lcd.size, color)

            # 中央に色の名前を描画
            draw = ImageDraw.Draw(solid_image)
            text = f"{name}"
            text_bbox = draw.textbbox((0, 0), text, font=font)
            text_width = text_bbox[2] - text_bbox[0]
            text_height = text_bbox[3] - text_bbox[1]
            text_x = (lcd.size.width - text_width) // 2
            text_y = (lcd.size.height - text_height) // 2

            # テキストの色を背景色と区別できるように設定
            text_color = (
                (0, 0, 0) if name != "Black" else (255, 255, 255)
            )  # 黒背景には白文字、それ以外は黒文字
            draw.text((text_x, text_y), text, fill=text_color, font=font)

            lcd.display(solid_image)
            time.sleep(3)

        print("bgr=False (RGB順) でテストします (各3秒間)")
        lcd.close()  # 既存のLCDインスタンスを閉じる

        with ST7789V(
            invert=True,
            bgr=False,  # RGBカラー順序をテスト
            debug=False,
        ) as lcd_rgb:
            print("RGB順ディスプレイ初期化完了")
            for name, color in colors.items():
                print(f"RGB順で {name} の画面を表示します (3秒間)")
                solid_image = Image.new("RGB", lcd_rgb.size, color)
                draw = ImageDraw.Draw(solid_image)
                text = f"RGB {name}"
                text_bbox = draw.textbbox((0, 0), text, font=font)
                text_width = text_bbox[2] - text_bbox[0]
                text_height = text_bbox[3] - text_bbox[1]
                text_x = (lcd_rgb.size.width - text_width) // 2
                text_y = (lcd_rgb.size.height - text_height) // 2
                text_color = (0, 0, 0) if name != "Black" else (255, 255, 255)
                draw.text((text_x, text_y), text, fill=text_color, font=font)

                lcd_rgb.display(solid_image)
                time.sleep(3)

        print("テスト終了。")

except RuntimeError as e:
    print(f"エラー: {e}")
except KeyboardInterrupt:
    print("スクリプトがユーザーによって中断されました。")
