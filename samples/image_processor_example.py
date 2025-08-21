import time
import os
from pi0disp import ST7789V, ImageProcessor
from PIL import Image

# スクリプト自身のディレクトリを取得し、それに基づいて画像パスを構築
script_dir = os.path.dirname(os.path.abspath(__file__))
IMAGE_PATH = os.path.join(script_dir, "my_photo.jpg")  # 表示したい画像ファイルのパス

def main():
    try:
        source_image = Image.open(IMAGE_PATH)
    except FileNotFoundError:
        print(f"エラー: 画像ファイル '{IMAGE_PATH}' が見つかりません。")
        return

    processor = ImageProcessor()

    try:
        with ST7789V() as lcd:
            print("1. 元の画像を画面サイズに合わせて表示します (containモード)...")
            
            # アスペクト比を維持してリサイズ
            resized_image = processor.resize_with_aspect_ratio(
                source_image,
                lcd.width,
                lcd.height,
                fit_mode="contain"
            )
            lcd.display(resized_image)
            time.sleep(5)

            print("2. ガンマ補正を適用して少し明るくします...")
            
            # ガンマ補正を適用
            corrected_image = processor.apply_gamma(resized_image, gamma=0.5)
            lcd.display(corrected_image)
            time.sleep(5)

    except Exception as e:
        print(f"ディスプレイ処理中にエラーが発生しました: {e}")

if __name__ == "__main__":
    main()
    print("完了しました。")
