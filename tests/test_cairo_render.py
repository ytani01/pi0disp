# -*- coding: utf-8 -*-
import cairo
import numpy as np
from PIL import Image


def test_cairo_to_pil_conversion():
    width, height = 100, 100
    # Cairo Surface 作成 (ARGB32)
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, width, height)
    ctx = cairo.Context(surface)

    # 背景を黒で塗りつぶし
    ctx.set_source_rgb(0, 0, 0)
    ctx.paint()

    # 白い円を描画 (アンチエイリアス有効)
    ctx.set_source_rgb(1, 1, 1)
    ctx.arc(50, 50, 40, 0, 2 * 3.14159)
    ctx.fill()

    # Surface -> NumPy -> PIL
    buf = surface.get_data()
    data = np.ndarray(shape=(height, width, 4), dtype=np.uint8, buffer=buf)
    # BGRA -> RGB (CairoのFORMAT_ARGB32はリトルエンディアンでBGRA)
    img = Image.fromarray(data[:, :, :3], "RGB")
    # チャンネルの入れ替え (B,G,R -> R,G,B)
    b, g, r = img.split()
    img = Image.merge("RGB", (r, g, b))

    assert img.size == (100, 100)

    # アンチエイリアスの確認
    # 円の境界付近のピクセルを取得し、0(黒)でも255(白)でもない値があるか確認
    pixels = np.array(img)
    has_intermediate = np.any((pixels > 10) & (pixels < 245))
    assert has_intermediate, "Cairo rendering should have anti-aliasing"
