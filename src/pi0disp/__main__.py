#
# (c) 2025 Yoichi Tanibayashi
#
import time

from PIL import Image

from . import ST7789V, __version__

print(f"ST7789V({__version__}) ドライバテスト開始")

try:
    # SPI速度を安定していた40MHzに戻してテスト
    with ST7789V(speed_hz=40000000) as lcd:
        print("初期化成功。新しいdisplay()メソッドで画面を青色で塗りつぶします...")
        
        # 青一色のPIL Imageオブジェクトを作成
        img = Image.new("RGB", (lcd.width, lcd.height), "blue")
            
        # 新しいdisplayメソッドで描画
        lcd.display(img)
            
        time.sleep(3)
        print("テスト完了")
except Exception as e:
    print(f"エラーが発生しました: {e}")
