#!/usr/bin/env python3
#
# (c) 2025 Yoichi Tanibayashi
#
"""
LCD Check Program (Optimized for 320x240)
最小限の表示で正しい設定を特定するためのプログラム。
"""
import os
from PIL import Image, ImageDraw, ImageFont
from pi0disp.disp.st7789v import ST7789V

def get_font(size):
    """ システムからフォントを探して返す """
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()

def draw_test_pattern(draw, w, h, invert, bgr, index):
    """ テストパターンを描画する """
    # 背景
    draw.rectangle([0, 0, w, h], fill="black")
    
    # 色帯 (高さを少し抑える)
    bh = h // 8
    draw.rectangle([0, 0,    w, bh],   fill="red")
    draw.rectangle([0, bh,   w, bh*2], fill="green")
    draw.rectangle([0, bh*2, w, bh*3], fill="blue")
    
    # テキスト設定
    f_mid = get_font(20)
    f_sm  = get_font(16)
        
    # 中央付近に設定を表示
    draw.text((15, bh*3 + 15), f"TEST {index}/4", fill="white", font=f_mid)
    
    conf_text = f"inv={invert}, bgr={bgr}"
    draw.text((15, bh*3 + 45), conf_text, fill="cyan", font=f_mid)
    
    # 下部にガイド
    draw.text((15, h - 55), "If R/G/B & Black look OK,", fill="gray", font=f_sm)
    draw.text((15, h - 35), "Use these values in TOML.", fill="yellow", font=f_sm)

def main():
    disp = ST7789V(rotation=90)
    width, height = disp.size.width, disp.size.height
    
    tests = [
        {"invert": True,  "bgr": False},
        {"invert": True,  "bgr": True},
        {"invert": False, "bgr": False},
        {"invert": False, "bgr": True},
    ]
    
    print("\n--- LCD Check (320x240) ---")
    print("各設定を順に表示します。")
    print("『背景が黒』『上から赤・緑・青』に見えるものを探してください。")
    
    try:
        for i, t in enumerate(tests):
            idx = i + 1
            print(f"[{idx}/4] inv={t['invert']}, bgr={t['bgr']}")
            
            # ディスプレイ更新
            disp._invert = t["invert"]
            disp._bgr = t["bgr"]
            disp.init_display()
            disp.set_rotation(disp.rotation)
            
            # 画像作成
            img = Image.new("RGB", (width, height), "black")
            d = ImageDraw.Draw(img)
            draw_test_pattern(d, width, height, t["invert"], t["bgr"], idx)
            
            disp.display(img)
            
            if i < len(tests) - 1:
                input("Next (Enter)...")
            else:
                input("Finish (Enter).")

    finally:
        disp.close()

if __name__ == "__main__":
    main()
