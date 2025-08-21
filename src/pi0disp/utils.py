# -*- coding: utf-8 -*-
"""
pi0disp プロジェクト全体で利用される高速化されたユーティリティ関数群。
"""
import numpy as np


# グローバルなルックアップテーブル（初期化時に一度だけ計算）
_R_SHIFT_TABLE = None
_G_SHIFT_TABLE = None  
_B_SHIFT_TABLE = None

def _init_lookup_tables():
    """RGB565変換用のルックアップテーブルを初期化"""
    global _R_SHIFT_TABLE, _G_SHIFT_TABLE, _B_SHIFT_TABLE
    if _R_SHIFT_TABLE is None:
        _R_SHIFT_TABLE = np.arange(256, dtype=np.uint16) >> 3
        _G_SHIFT_TABLE = (np.arange(256, dtype=np.uint16) >> 2) << 5  
        _B_SHIFT_TABLE = (np.arange(256, dtype=np.uint16) >> 3) << 11


def pil_to_rgb565_bytes(img):
    """PIL.Image → RGB565のバイト列に変換 (最適化版)"""
    # ルックアップテーブルを初期化
    _init_lookup_tables()
    
    # RGB画像であることを確認
    if img.mode != "RGB":
        img = img.convert("RGB")
        
    # NumPy配列に変換
    np_img = np.array(img, dtype=np.uint8)
    
    # ルックアップテーブルを使用した高速変換
    r_vals = _R_SHIFT_TABLE[np_img[:, :, 0]]
    g_vals = _G_SHIFT_TABLE[np_img[:, :, 1]]
    b_vals = _B_SHIFT_TABLE[np_img[:, :, 2]]
    
    # RGB565形式にパック
    rgb565 = r_vals | g_vals | b_vals
    
    # ビッグエンディアン形式でバイト列に変換
    return rgb565.astype('>u2').tobytes()


def pil_to_rgb565_bytes_region(img, x0, y0, x1, y1):
    """指定領域のみをRGB565に変換（差分更新最適化用）"""
    _init_lookup_tables()
    
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # 領域をクロップしてから変換（メモリ効率が良い）
    region = img.crop((x0, y0, x1, y1))
    np_img = np.array(region, dtype=np.uint8)
    
    r_vals = _R_SHIFT_TABLE[np_img[:, :, 0]]
    g_vals = _G_SHIFT_TABLE[np_img[:, :, 1]]
    b_vals = _B_SHIFT_TABLE[np_img[:, :, 2]]
    
    rgb565 = r_vals | g_vals | b_vals
    return rgb565.astype('>u2').tobytes()


def merge_bboxes(bbox1, bbox2):
    """2つのバウンディングボックスをマージ（高速化版）"""
    if bbox1 is None:
        return bbox2
    if bbox2 is None:
        return bbox1
    
    # タプルアンパックを使用して高速化
    x1_min, y1_min, x1_max, y1_max = bbox1
    x2_min, y2_min, x2_max, y2_max = bbox2
    
    return (
        min(x1_min, x2_min),
        min(y1_min, y2_min), 
        max(x1_max, x2_max),
        max(y1_max, y2_max)
    )


def optimize_dirty_regions(regions, max_regions=8, merge_threshold=50):
    """
    ダーティ領域のリストを最適化する
    - 近接する小さな領域をマージ
    - 領域数を制限してSPI転送回数を削減
    """
    if not regions or len(regions) <= 1:
        return regions
        
    # 面積でソート（小さいものから処理）
    sorted_regions = sorted(regions, key=lambda r: (r[2]-r[0]) * (r[3]-r[1]))
    merged = []
    
    while sorted_regions and len(merged) < max_regions - 1:
        current = sorted_regions.pop(0)
        merged_any = False
        
        # 既存のマージ済み領域と結合可能かチェック
        for i, existing in enumerate(merged):
            if _regions_should_merge(current, existing, merge_threshold):
                merged[i] = merge_bboxes(current, existing)
                merged_any = True
                break
                
        if not merged_any:
            # 残りの領域と結合可能かチェック
            for j, other in enumerate(sorted_regions):
                if _regions_should_merge(current, other, merge_threshold):
                    current = merge_bboxes(current, other)
                    sorted_regions.pop(j)
                    break
            merged.append(current)
    
    # 残りの領域は一つの大きな領域にまとめる
    if sorted_regions:
        if merged:
            # 全ての領域を含む最小の矩形を計算
            all_regions = merged + sorted_regions
            merged = [_compute_bounding_rect(all_regions)]
        else:
            merged = [_compute_bounding_rect(sorted_regions)]
    
    return merged


def _regions_should_merge(region1, region2, threshold):
    """2つの領域をマージすべきかどうかを判定"""
    x1_min, y1_min, x1_max, y1_max = region1
    x2_min, y2_min, x2_max, y2_max = region2
    
    # 重複または近接している場合はマージ
    x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
    y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
    
    # X軸またはY軸で重複/近接している場合
    x_distance = max(0, max(x1_min, x2_min) - min(x1_max, x2_max))
    y_distance = max(0, max(y1_min, y2_min) - min(y1_max, y2_max))
    
    return (x_overlap > 0 or x_distance <= threshold) and \
           (y_overlap > 0 or y_distance <= threshold)


def _compute_bounding_rect(regions):
    """複数の領域を含む最小の矩形を計算"""
    if not regions:
        return None
        
    min_x = min(r[0] for r in regions)
    min_y = min(r[1] for r in regions) 
    max_x = max(r[2] for r in regions)
    max_y = max(r[3] for r in regions)
    
    return (min_x, min_y, max_x, max_y)


def clamp_region(region, width, height):
    """領域を画面境界内にクランプする"""
    return (
        max(0, region[0]),
        max(0, region[1]),
        min(width, region[2]), 
        min(height, region[3])
    )