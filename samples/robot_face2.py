import os
import random
import sys
import time

from PIL import Image, ImageOps

# ST7789ライブラリのインポート
# インストール: pip install st7789
try:
    from pi0disp.disp.st7789v import ST7789V
except ImportError:
    print("エラー: 'st7789' ライブラリが見つかりません。")
    print("インストールコマンド: pip install st7789")
    sys.exit(1)

# --- 設定 ---
SCREEN_WIDTH = 320
SCREEN_HEIGHT = 240
IMAGE_DIR = "./samples/robot_face2_images"  # 画像フォルダ
DISPLAY_TIME = 5  # 切り替え時間(秒)

# --- GPIOピン設定 (BCM番号) ---
# お使いのHATや配線に合わせて変更してください
SPI_PORT = 0
SPI_CS = 0  # CE0
SPI_SPEED_HZ = 40 * 1000 * 1000  # 40MHz

DC_PIN = 9  # Data/Command
RST_PIN = 25  # Reset
BL_PIN = 13  # Backlight (接続していない場合はNoneにする)


def main():
    """Main."""
    print("ディスプレイを初期化中...")

    # ST7789の初期化
    disp = ST7789V()

    # バックライトの初期化と画面クリア
    # disp.begin()

    # 画像ファイルリストの取得
    if not os.path.exists(IMAGE_DIR):
        print(f"エラー: '{IMAGE_DIR}' フォルダが見つかりません。")
        return

    image_files = [
        f
        for f in os.listdir(IMAGE_DIR)
        if f.lower().endswith((".png", ".jpg", ".jpeg", ".bmp", ".gif"))
    ]

    if not image_files:
        print("画像ファイルが見つかりません。")
        return

    print("スライドショーを開始します (Ctrl+C で終了)")

    try:
        while True:
            # ランダムに画像を選択
            filename = random.choice(image_files)
            filepath = os.path.join(IMAGE_DIR, filename)

            try:
                # 画像を開く
                img: Image.Image = Image.open(filepath)

                # --- アスペクト比を維持してリサイズ & 黒帯追加 ---
                # 320x240のキャンバスの中央に画像を配置し、余白を黒(0,0,0)で埋める
                img = ImageOps.pad(
                    img,
                    (SCREEN_WIDTH, SCREEN_HEIGHT),
                    color=(0, 0, 0),
                    centering=(0.5, 0.5),
                )

                # ディスプレイに画像データを転送
                print(f"Displaying: {filename}")
                disp.display(img)

            except Exception as e:
                print(f"画像読み込みエラー ({filename}): {e}")

            time.sleep(DISPLAY_TIME)

    except KeyboardInterrupt:
        print("\n終了します。")


if __name__ == "__main__":
    main()
