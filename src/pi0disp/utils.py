# -*- coding: utf-8 -*-
"""
pi0disp プロジェクト全体で利用されるユーティリティ関数群。
"""
import numpy as np


def pil_to_rgb565_bytes(img):
    """PIL.Image → RGB565のバイト列に変換 (numpyを使った高速版)"""
    np_img = np.array(img, dtype=np.uint8)
    r = (np_img[:, :, 0] >> 3).astype(np.uint16)
    g = (np_img[:, :, 1] >> 2).astype(np.uint16)
    b = (np_img[:, :, 2] >> 3).astype(np.uint16)
    rgb565 = (r << 11) | (g << 5) | b
    return rgb565.byteswap().tobytes()

def merge_bboxes(bbox1, bbox2):
    """2つのバウンディングボックスをマージして、両方を含む最小のボックスを返す"""
    if not bbox1:
        return bbox2
    if not bbox2:
        return bbox1
    return (
        min(bbox1[0], bbox2[0]),
        min(bbox1[1], bbox2[1]),
        max(bbox1[2], bbox2[2]),
        max(bbox1[3], bbox2[3]),
    )
