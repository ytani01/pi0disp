# -*- coding: utf-8 -*-
"""
performance_core.py - パフォーマンス最適化のためのコアモジュール

このモジュールは、RGBからRGB565への高速変換など、描画パフォーマンスに
直結するコアな最適化ロジックを提供します。
"""

import numpy as np


class ColorConverter:
    """
    RGB から RGB565 への高速変換とガンマ補正を担当するクラス。
    NumPy を利用したルックアップテーブル (LUT) により高速化されています。
    """

    __slots__ = ("_r_lut", "_g_lut", "_b_lut", "_gamma_lut")

    def __init__(self, gamma: float = 2.2):
        """
        ColorConverter を初期化し、LUTを生成します。

        Args:
            gamma (float): ガンマ補正値。デフォルトは 2.2。
        """
        # RGB565 変換用 LUT (8bit -> 5bit/6bit/5bit)
        self._r_lut = (np.arange(256, dtype=np.uint16) >> 3) << 11
        self._g_lut = (np.arange(256, dtype=np.uint16) >> 2) << 5
        self._b_lut = np.arange(256, dtype=np.uint16) >> 3
        self._gamma_lut = np.array([], dtype=np.uint8)
        self.set_gamma(gamma)

    def set_gamma(self, gamma: float):
        """
        ガンマ補正テーブルを更新します。

        Args:
            gamma (float): 新しいガンマ補正値。
        """
        self._gamma_lut = np.array(
            [int(255 * ((i / 255.0) ** gamma)) for i in range(256)],
            dtype=np.uint8,
        )

    def convert(self, rgb_array: np.ndarray, apply_gamma: bool = False) -> bytes:
        """
        RGB NumPy 配列を大端エンディアンの RGB565 バイト列に変換します。

        Args:
            rgb_array: Shape (H, W, 3) の NumPy 配列。
            apply_gamma (bool): 変換前にガンマ補正を適用するかどうか。

        Returns:
            RGB565 形式のバイト列。
        """
        if apply_gamma:
            rgb_array = self._gamma_lut[rgb_array]

        r = self._r_lut[rgb_array[:, :, 0]]
        g = self._g_lut[rgb_array[:, :, 1]]
        b = self._b_lut[rgb_array[:, :, 2]]

        # Big-endian 16-bit
        return (r | g | b).astype(">u2").tobytes()


class RegionOptimizer:
    """
    複数の描画領域 (矩形) をマージし、SPI転送回数を最適化するクラス。
    """

    @staticmethod
    def merge_regions(regions, area_threshold: float = 1.5):
        """
        重なり合っている、または近い矩形をマージします。

        Args:
            regions: (x, y, w, h) のリスト。
            area_threshold (float): マージ後の面積が (元の面積合計 * threshold)
                                     以下ならマージする。デフォルトは 1.5。

        Returns:
            最適化された (x, y, w, h) のリスト。
        """
        if not regions:
            return []

        # (x1, y1, x2, y2) 形式に変換
        work_regions = []
        for x, y, w, h in regions:
            work_regions.append([x, y, x + w, y + h])

        changed = True
        while changed:
            changed = False
            new_regions = []
            while work_regions:
                r1 = work_regions.pop(0)
                merged = False
                for i in range(len(work_regions)):
                    r2 = work_regions[i]

                    # 最小包含矩形 (MBR)
                    nx1 = min(r1[0], r2[0])
                    ny1 = min(r1[1], r2[1])
                    nx2 = max(r1[2], r2[2])
                    ny2 = max(r1[3], r2[3])

                    # 面積判定
                    a1 = (r1[2] - r1[0]) * (r1[3] - r1[1])
                    a2 = (r2[2] - r2[0]) * (r2[3] - r2[1])
                    na = (nx2 - nx1) * (ny2 - ny1)

                    if na <= (a1 + a2) * area_threshold:
                        work_regions[i] = [nx1, ny1, nx2, ny2]
                        merged = True
                        changed = True
                        break

                if not merged:
                    new_regions.append(r1)
            work_regions = new_regions

        # (x, y, w, h) 形式に戻す
        return [(r[0], r[1], r[2] - r[0], r[3] - r[1]) for r in work_regions]
