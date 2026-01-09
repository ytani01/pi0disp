# samples/sample_perf_core.py
"""
pi0disp.utils.performance_core と関連ユーティリティの使用例
"""
import numpy as np
from PIL import Image

# 1. 必要なモジュールをインポート
from pi0disp.utils.performance_core import ColorConverter
from pi0disp.utils.utils import clamp_region, merge_bboxes, pil_to_rgb565_bytes


def main():
    """メインのサンプル実行関数"""
    print("--- performance_core and utils sample ---")

    # --- ColorConverter ---
    print("\n[1] ColorConverter")
    # 4x4のRGB画像 (NumPy配列) を作成
    img_array = np.zeros((4, 4, 3), dtype=np.uint8)
    img_array[:, :, 0] = np.linspace(0, 255, 4, dtype=np.uint8)  # Red
    img_array[:, :, 1] = np.linspace(0, 255, 4, dtype=np.uint8)[:, np.newaxis]  # Green

    # コンバータを作成し、RGB565に変換
    converter = ColorConverter()
    rgb565_bytes = converter.convert(img_array)
    print(f"4x4 Image converted to {len(rgb565_bytes)} bytes of RGB565 data.")
    print(f"First 4 bytes (2 pixels): {rgb565_bytes[:4].hex()}")

    # --- pil_to_rgb565_bytes ---
    print("\n[2] pil_to_rgb565_bytes")
    pil_img = Image.fromarray(img_array, "RGB")
    util_bytes = pil_to_rgb565_bytes(pil_img)
    assert rgb565_bytes == util_bytes
    print("Successfully converted PIL Image to RGB565 bytes.")

    # --- BBox Utilities ---
    print("\n[3] Bounding Box Utilities")
    bbox1 = (10, 20, 30, 40)
    bbox2 = (25, 35, 45, 55)
    merged = merge_bboxes(bbox1, bbox2)
    print(f"Merged {bbox1} and {bbox2} -> {merged}")

    screen_size = (50, 50)
    outside_region = (-10, -10, 60, 60)
    clamped = clamp_region(outside_region, *screen_size)
    print(f"Clamped {outside_region} to screen {screen_size} -> {clamped}")


if __name__ == "__main__":
    main()
