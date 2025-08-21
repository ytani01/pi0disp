# -*- coding: utf-8 -*-
"""
pi0disp プロジェクト用ユーティリティ関数群（モジュラー最適化版）
performance_coreの汎用機能を活用
"""
import numpy as np
from PIL import Image
from typing import List, Tuple, Optional, Union

from .performance_core import (
    ColorConverter, RegionOptimizer, MemoryPool,
    LookupTableCache, create_embedded_optimizer
)

# グローバルな最適化オブジェクト（モジュールレベルで共有）
_GLOBAL_OPTIMIZERS = None

def _get_global_optimizers():
    """グローバル最適化オブジェクトを取得（遅延初期化）"""
    global _GLOBAL_OPTIMIZERS
    if _GLOBAL_OPTIMIZERS is None:
        _GLOBAL_OPTIMIZERS = create_embedded_optimizer()
    return _GLOBAL_OPTIMIZERS


def pil_to_rgb565_bytes(img: Image.Image) -> bytes:
    """
    PIL.Image → RGB565のバイト列に変換 (汎用最適化版)
    
    :param img: 変換対象のPIL画像
    :return: RGB565形式のバイト列
    """
    optimizers = _get_global_optimizers()
    
    # RGB画像であることを確認
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # NumPy配列に変換
    np_img = np.array(img, dtype=np.uint8)
    
    # 汎用カラーコンバータを使用
    return optimizers['color_converter'].rgb_to_rgb565_fast(np_img)


def pil_to_rgb565_bytes_region(img: Image.Image, 
                              x0: int, y0: int, x1: int, y1: int) -> bytes:
    """
    指定領域のみをRGB565に変換（差分更新最適化用）
    
    :param img: 変換対象のPIL画像
    :param x0, y0, x1, y1: 変換領域の座標
    :return: RGB565形式のバイト列
    """
    optimizers = _get_global_optimizers()
    
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # 領域をクロップしてから変換（メモリ効率向上）
    region = img.crop((x0, y0, x1, y1))
    np_img = np.array(region, dtype=np.uint8)
    
    return optimizers['color_converter'].rgb_to_rgb565_fast(np_img)


def merge_bboxes(bbox1: Optional[Tuple[int, int, int, int]], 
                bbox2: Optional[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    """
    2つのバウンディングボックスをマージ（汎用最適化版）
    
    :param bbox1: 第1のバウンディングボックス (x0, y0, x1, y1) or None
    :param bbox2: 第2のバウンディングボックス (x0, y0, x1, y1) or None
    :return: マージされたバウンディングボックス or None
    """
    optimizers = _get_global_optimizers()
    
    if bbox1 is None:
        return bbox2
    if bbox2 is None:
        return bbox1
    
    # RegionOptimizerの機能を使用
    return optimizers['region_optimizer']._merge_two_regions(bbox1, bbox2)


def optimize_dirty_regions(regions: List[Tuple[int, int, int, int]], 
                          max_regions: int = 8, 
                          merge_threshold: int = 50) -> List[Tuple[int, int, int, int]]:
    """
    ダーティ領域のリストを最適化（汎用最適化版）
    
    :param regions: 最適化対象の領域リスト
    :param max_regions: 最大出力領域数
    :param merge_threshold: マージ判定の距離閾値
    :return: 最適化された領域リスト
    """
    optimizers = _get_global_optimizers()
    
    return optimizers['region_optimizer'].merge_regions(
        regions, max_regions, merge_threshold
    )


def clamp_region(region: Tuple[int, int, int, int], 
                width: int, height: int) -> Tuple[int, int, int, int]:
    """
    領域を画面境界内にクランプ（汎用最適化版）
    
    :param region: クランプ対象の領域 (x0, y0, x1, y1)
    :param width: 画面幅
    :param height: 画面高さ
    :return: クランプされた領域
    """
    optimizers = _get_global_optimizers()
    
    return optimizers['region_optimizer'].clamp_region(region, width, height)


def create_memory_buffer(size: int) -> Union[bytearray, bytes]:
    """
    メモリプールからバッファを取得
    
    :param size: 必要なバッファサイズ
    :return: バッファオブジェクト
    """
    optimizers = _get_global_optimizers()
    return optimizers['memory_pool'].get_buffer(size)


def return_memory_buffer(buffer: Union[bytearray, bytes], size_hint: Optional[int] = None):
    """
    バッファをメモリプールに返却
    
    :param buffer: 返却するバッファ
    :param size_hint: サイズヒント（パフォーマンス向上用）
    """
    optimizers = _get_global_optimizers()
    optimizers['memory_pool'].return_buffer(buffer, size_hint)


def get_performance_stats() -> dict:
    """
    ユーティリティモジュールのパフォーマンス統計を取得
    
    :return: 統計情報辞書
    """
    optimizers = _get_global_optimizers()
    return {
        'memory_pool_stats': optimizers['memory_pool'].get_stats(),
        'color_converter_available': True,
        'region_optimizer_available': True
    }


def reset_performance_stats():
    """パフォーマンス統計をリセット"""
    optimizers = _get_global_optimizers()
    optimizers['memory_pool'].clear()


class ImageProcessor:
    """
    画像処理ユーティリティクラス
    様々な画像変換・最適化処理を提供
    """
    
    def __init__(self, optimization_level: str = "balanced"):
        """
        :param optimization_level: 最適化レベル ("low", "balanced", "high")
        """
        self.optimizers = create_embedded_optimizer()
        self.optimization_level = optimization_level
        
    def resize_with_aspect_ratio(self, 
                                img: Image.Image, 
                                target_width: int, 
                                target_height: int,
                                fit_mode: str = "contain") -> Image.Image:
        """
        アスペクト比を保持してリサイズ
        
        :param img: リサイズ対象画像
        :param target_width: 目標幅
        :param target_height: 目標高さ
        :param fit_mode: フィットモード ("contain", "cover", "stretch")
        :return: リサイズされた画像
        """
        if fit_mode == "stretch":
            return img.resize((target_width, target_height))
        
        # アスペクト比計算
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if fit_mode == "contain":
            if img_ratio > target_ratio:
                # 幅に合わせる
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                # 高さに合わせる
                new_height = target_height
                new_width = int(target_height * img_ratio)
        else:  # cover
            if img_ratio > target_ratio:
                # 高さに合わせる
                new_height = target_height
                new_width = int(target_height * img_ratio)
            else:
                # 幅に合わせる
                new_width = target_width
                new_height = int(target_width / img_ratio)
        
        resized = img.resize((new_width, new_height))
        
        # 中央に配置
        if fit_mode == "contain":
            result = Image.new("RGB", (target_width, target_height), (0, 0, 0))
            paste_x = (target_width - new_width) // 2
            paste_y = (target_height - new_height) // 2
            result.paste(resized, (paste_x, paste_y))
            return result
        else:  # cover
            crop_x = (new_width - target_width) // 2
            crop_y = (new_height - target_height) // 2
            return resized.crop((crop_x, crop_y, crop_x + target_width, crop_y + target_height))
    
    def apply_gamma_correction(self, 
                              img: Image.Image, 
                              gamma: float = 2.2) -> Image.Image:
        """
        ガンマ補正を適用
        
        :param img: 補正対象画像
        :param gamma: ガンマ値
        :return: ガンマ補正済み画像
        """
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        np_img = np.array(img, dtype=np.uint8)
        corrected = self.optimizers['color_converter'].apply_gamma_correction(np_img, gamma)
        
        return Image.fromarray(corrected, "RGB")
    
    def create_gradient_background(self, 
                                  width: int, 
                                  height: int,
                                  colors: List[Tuple[int, int, int]] = None,
                                  direction: str = "vertical") -> Image.Image:
        """
        グラデーション背景画像を生成
        
        :param width: 画像幅
        :param height: 画像高さ
        :param colors: グラデーション色のリスト [(r,g,b), ...]
        :param direction: グラデーション方向 ("vertical", "horizontal", "diagonal")
        :return: グラデーション画像
        """
        if colors is None:
            colors = [(0, 0, 0), (64, 128, 255)]
        
        img = Image.new("RGB", (width, height))
        pixels = img.load()
        
        for y in range(height):
            for x in range(width):
                if direction == "vertical":
                    ratio = y / (height - 1) if height > 1 else 0
                elif direction == "horizontal":
                    ratio = x / (width - 1) if width > 1 else 0
                else:  # diagonal
                    ratio = (x + y) / (width + height - 2) if (width + height) > 2 else 0
                
                ratio = min(1.0, max(0.0, ratio))
                
                # 線形補間
                if len(colors) == 2:
                    r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
                    g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
                    b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
                else:
                    # 複数色の場合は最初の2色のみ使用
                    r = int(colors[0][0] * (1 - ratio) + colors[1][0] * ratio)
                    g = int(colors[0][1] * (1 - ratio) + colors[1][1] * ratio)
                    b = int(colors[0][2] * (1 - ratio) + colors[1][2] * ratio)
                
                pixels[x, y] = (r, g, b)
        
        return img


# 後方互換性のための関数エイリアス
def merge_bboxes_legacy(bbox1, bbox2):
    """後方互換性のためのエイリアス"""
    return merge_bboxes(bbox1, bbox2)


# モジュール初期化時にグローバル最適化オブジェクトを準備
def initialize_optimizers():
    """最適化オブジェクトを明示的に初期化"""
    global _GLOBAL_OPTIMIZERS
    if _GLOBAL_OPTIMIZERS is None:
        _GLOBAL_OPTIMIZERS = create_embedded_optimizer()


# オプション: モジュールインポート時に初期化を実行
# initialize_optimizers()
