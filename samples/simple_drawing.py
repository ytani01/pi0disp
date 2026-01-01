"""
図形、テキスト、複数の色を使用した基本的な描画サンプル。
"""

import time

from PIL import Image, ImageDraw  # 描画用ライブラリ
from PIL.ImageFont import FreeTypeFont, ImageFont, load_default, truetype

from pi0disp import ST7789V  # ST7789Vドライバー

FONT_PATH = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


def main() -> None:
    #
    # 1. ディスプレイの初期化 (横向き)
    #
    # pi0disp.toml の設定が自動適用されます。
    #
    disp = ST7789V(rotation=ST7789V.EAST)

    #
    # 2. 描画用キャンバスの作成
    #
    img = Image.new("RGB", (disp.width, disp.height), "black")
    draw = ImageDraw.Draw(img)

    #
    # 3. 図形の描画
    #
    # 直線
    draw.line([0, 0, disp.width - 1, disp.height - 1], fill="cyan", width=15)
    # 四角形
    draw.rectangle([20, 20, 120, 120], fill="blue", outline="yellow", width=5)
    # 円
    draw.ellipse([80, 80, 200, 200], fill="red", outline="white", width=5)

    #
    # 4. テキストの描画
    #
    font: FreeTypeFont | ImageFont | None = None
    try:
        font = truetype(FONT_PATH, 40)
    except OSError:
        # フォントがない場合は、デフォルトの小さなフォント
        font = load_default()

    text = "pi0disp"
    draw.text((40, disp.height / 2), text, fill="green", font=font, width=2)

    #
    # 5. ディスプレイに表示
    #
    disp.display(img)

    print("Displaying for 5 seconds...")
    time.sleep(5)

    #
    # 6. 終了処理
    #
    disp.close()


if __name__ == "__main__":
    main()
