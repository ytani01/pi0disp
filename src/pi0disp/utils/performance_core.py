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

    def convert(
        self, rgb_array: np.ndarray, apply_gamma: bool = False
    ) -> bytes:
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
