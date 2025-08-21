# -*- coding: utf-8 -*-
"""
performance_core.py - 汎用パフォーマンス最適化モジュール

組み込みシステム向けの汎用的なパフォーマンス最適化機能を提供します。
Raspberry Pi Zero 2Wなどのリソース制約のある環境での使用を想定。
"""
import time
import threading
from collections import deque
from typing import Optional, List, Tuple, Union, Callable, Any
from abc import ABC, abstractmethod

import numpy as np


class MemoryPool:
    """
    メモリプール管理クラス
    頻繁にアロケーションされるバッファを再利用してGC負荷を削減
    """
    def __init__(self, max_pools: int = 8, buffer_factory: Callable[[int], Any] = bytearray):
        """
        :param max_pools: プールに保持する最大バッファ数
        :param buffer_factory: バッファ生成関数（デフォルト: bytearray）
        """
        self._pools = {}  # サイズ別のプール
        self._max_pools = max_pools
        self._buffer_factory = buffer_factory
        self._lock = threading.Lock()
        self._stats = {'hits': 0, 'misses': 0, 'created': 0}

    def get_buffer(self, size: int, exact_size: bool = False):
        """
        指定サイズのバッファを取得
        
        :param size: 必要なバッファサイズ
        :param exact_size: True の場合、正確なサイズのバッファのみ返す
        :return: バッファオブジェクト
        """
        with self._lock:
            if exact_size:
                if size in self._pools and self._pools[size]:
                    self._stats['hits'] += 1
                    return self._pools[size].pop()
            else:
                # より大きなサイズのバッファも利用可能
                for pool_size in sorted(self._pools.keys()):
                    if pool_size >= size and self._pools[pool_size]:
                        self._stats['hits'] += 1
                        return self._pools[pool_size].pop()
            
            # プールにない場合は新規作成
            self._stats['misses'] += 1
            self._stats['created'] += 1
            return self._buffer_factory(size)

    def return_buffer(self, buffer, size_hint: Optional[int] = None):
        """
        バッファをプールに返却
        
        :param buffer: 返却するバッファ
        :param size_hint: バッファサイズのヒント（パフォーマンス向上用）
        """
        if size_hint is None:
            size_hint = len(buffer)
            
        with self._lock:
            if size_hint not in self._pools:
                self._pools[size_hint] = deque(maxlen=self._max_pools)
            
            if len(self._pools[size_hint]) < self._max_pools:
                self._pools[size_hint].append(buffer)

    def get_stats(self) -> dict:
        """プール使用統計を取得"""
        with self._lock:
            return self._stats.copy()

    def clear(self):
        """全プールをクリア"""
        with self._lock:
            self._pools.clear()
            self._stats = {'hits': 0, 'misses': 0, 'created': 0}


class LookupTableCache:
    """
    ルックアップテーブルキャッシュ
    計算コストの高い変換テーブルを事前計算・キャッシュ
    """
    _instances = {}
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, table_type: str) -> 'LookupTableCache':
        """シングルトンパターンでインスタンス取得"""
        with cls._lock:
            if table_type not in cls._instances:
                cls._instances[table_type] = cls(table_type)
            return cls._instances[table_type]

    def __init__(self, table_type: str):
        self.table_type = table_type
        self._tables = {}
        self._generators = {
            'rgb565': self._generate_rgb565_tables,
            'gamma': self._generate_gamma_tables,
            'brightness': self._generate_brightness_tables
        }

    def _generate_rgb565_tables(self) -> dict:
        """RGB565変換テーブル生成"""
        return {
            'r_shift': np.arange(256, dtype=np.uint16) >> 3,
            'g_shift': (np.arange(256, dtype=np.uint16) >> 2) << 5,
            'b_shift': (np.arange(256, dtype=np.uint16) >> 3) << 11
        }

    def _generate_gamma_tables(self, gamma: float = 2.2) -> dict:
        """ガンマ補正テーブル生成"""
        gamma_table = np.array([
            int(255 * ((i / 255.0) ** (1.0 / gamma)))
            for i in range(256)
        ], dtype=np.uint8)
        return {'gamma_table': gamma_table}

    def _generate_brightness_tables(self, levels: int = 256) -> dict:
        """輝度調整テーブル生成"""
        brightness_tables = {}
        for level in range(levels):
            factor = level / (levels - 1)
            brightness_tables[level] = np.clip(
                (np.arange(256) * factor).astype(np.uint8), 0, 255
            )
        return {'brightness_tables': brightness_tables}

    def get_table(self, table_name: str, **kwargs):
        """テーブル取得（必要に応じて生成）"""
        cache_key = f"{table_name}_{hash(str(sorted(kwargs.items())))}"
        
        if cache_key not in self._tables:
            if self.table_type in self._generators:
                generated_tables = self._generators[self.table_type](**kwargs)
                if table_name in generated_tables:
                    self._tables[cache_key] = generated_tables[table_name]
                else:
                    raise KeyError(f"Table '{table_name}' not found in {self.table_type}")
            else:
                raise ValueError(f"Unknown table type: {self.table_type}")
        
        return self._tables[cache_key]


class RegionOptimizer:
    """
    矩形領域最適化クラス
    ダーティ領域のマージ・最適化を行い、描画効率を向上
    """
    
    @staticmethod
    def merge_regions(regions: List[Tuple[int, int, int, int]], 
                     max_regions: int = 8, 
                     merge_threshold: int = 50,
                     area_threshold: int = 1000) -> List[Tuple[int, int, int, int]]:
        """
        複数の矩形領域を最適化してマージ
        
        :param regions: 矩形領域のリスト [(x0, y0, x1, y1), ...]
        :param max_regions: 最大出力領域数
        :param merge_threshold: マージ判定の距離閾値
        :param area_threshold: 小領域統合の面積閾値
        :return: 最適化された領域リスト
        """
        if not regions or len(regions) <= 1:
            return regions

        # 無効な領域を除外
        valid_regions = [
            r for r in regions 
            if r[2] > r[0] and r[3] > r[1]
        ]
        
        if not valid_regions:
            return []

        # 面積でソート（小さいものから処理）
        sorted_regions = sorted(
            valid_regions, 
            key=lambda r: (r[2] - r[0]) * (r[3] - r[1])
        )
        
        merged = []
        
        while sorted_regions and len(merged) < max_regions - 1:
            current = sorted_regions.pop(0)
            merged_any = False
            
            # 既存のマージ済み領域と統合可能かチェック
            for i, existing in enumerate(merged):
                if RegionOptimizer._should_merge_regions(
                    current, existing, merge_threshold
                ):
                    merged[i] = RegionOptimizer._merge_two_regions(current, existing)
                    merged_any = True
                    break
            
            if not merged_any:
                # 残り領域と統合可能かチェック
                for j, other in enumerate(sorted_regions):
                    if RegionOptimizer._should_merge_regions(
                        current, other, merge_threshold
                    ):
                        current = RegionOptimizer._merge_two_regions(current, other)
                        sorted_regions.pop(j)
                        break
                merged.append(current)
        
        # 残りの領域をまとめる
        if sorted_regions:
            if merged:
                all_regions = merged + sorted_regions
                bounding_rect = RegionOptimizer._compute_bounding_rect(all_regions)
                merged = [bounding_rect]
            else:
                merged = [RegionOptimizer._compute_bounding_rect(sorted_regions)]
        
        return merged

    @staticmethod
    def _should_merge_regions(region1: Tuple[int, int, int, int],
                             region2: Tuple[int, int, int, int],
                             threshold: int) -> bool:
        """2つの領域をマージすべきかどうかを判定"""
        x1_min, y1_min, x1_max, y1_max = region1
        x2_min, y2_min, x2_max, y2_max = region2
        
        # 重複チェック
        x_overlap = max(0, min(x1_max, x2_max) - max(x1_min, x2_min))
        y_overlap = max(0, min(y1_max, y2_max) - max(y1_min, y2_min))
        
        # 距離チェック
        x_distance = max(0, max(x1_min, x2_min) - min(x1_max, x2_max))
        y_distance = max(0, max(y1_min, y2_min) - min(y1_max, y2_max))
        
        return ((x_overlap > 0 or x_distance <= threshold) and 
                (y_overlap > 0 or y_distance <= threshold))

    @staticmethod
    def _merge_two_regions(region1: Tuple[int, int, int, int],
                          region2: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """2つの領域をマージ"""
        return (
            min(region1[0], region2[0]),
            min(region1[1], region2[1]),
            max(region1[2], region2[2]),
            max(region1[3], region2[3])
        )

    @staticmethod
    def _compute_bounding_rect(regions: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
        """複数領域の外接矩形を計算"""
        if not regions:
            return (0, 0, 0, 0)
        
        return (
            min(r[0] for r in regions),
            min(r[1] for r in regions),
            max(r[2] for r in regions),
            max(r[3] for r in regions)
        )

    @staticmethod
    def clamp_region(region: Tuple[int, int, int, int],
                    width: int, height: int) -> Tuple[int, int, int, int]:
        """領域を画面境界内にクランプ"""
        return (
            max(0, region[0]),
            max(0, region[1]),
            min(width, region[2]),
            min(height, region[3])
        )


class PerformanceMonitor:
    """
    パフォーマンス監視クラス
    フレームレート、処理時間、メモリ使用量などを監視
    """
    
    def __init__(self, window_size: int = 60):
        """
        :param window_size: 統計計算用の履歴サイズ
        """
        self.window_size = window_size
        self._frame_times = deque(maxlen=window_size)
        self._process_times = deque(maxlen=window_size)
        self._last_frame_time = time.time()
        self._start_time = time.time()
        self._frame_count = 0

    def frame_start(self):
        """フレーム開始を記録"""
        current_time = time.time()
        if self._frame_count > 0:
            frame_time = current_time - self._last_frame_time
            self._frame_times.append(frame_time)
        self._last_frame_time = current_time
        self._frame_count += 1
        return current_time

    def frame_end(self, start_time: float):
        """フレーム終了を記録"""
        process_time = time.time() - start_time
        self._process_times.append(process_time)

    def get_fps(self) -> float:
        """現在のFPS取得"""
        if not self._frame_times:
            return 0.0
        return 1.0 / (sum(self._frame_times) / len(self._frame_times))

    def get_average_process_time(self) -> float:
        """平均処理時間取得"""
        if not self._process_times:
            return 0.0
        return sum(self._process_times) / len(self._process_times)

    def get_cpu_utilization(self, target_fps: float) -> float:
        """CPU使用率推定"""
        if not self._process_times:
            return 0.0
        avg_process_time = self.get_average_process_time()
        target_frame_time = 1.0 / target_fps
        return min(100.0, (avg_process_time / target_frame_time) * 100.0)

    def get_stats(self) -> dict:
        """全統計情報取得"""
        return {
            'fps': self.get_fps(),
            'avg_process_time': self.get_average_process_time(),
            'frame_count': self._frame_count,
            'uptime': time.time() - self._start_time,
            'cpu_utilization': self.get_cpu_utilization(30.0)  # 30FPS基準
        }


class AdaptiveChunking:
    """
    適応的チャンクサイズ管理
    システム性能に基づいてデータ転送サイズを動的調整
    """
    
    def __init__(self, initial_chunk_size: int = 4096,
                 min_chunk_size: int = 1024,
                 max_chunk_size: int = 16384):
        """
        :param initial_chunk_size: 初期チャンクサイズ
        :param min_chunk_size: 最小チャンクサイズ
        :param max_chunk_size: 最大チャンクサイズ
        """
        self.current_chunk_size = initial_chunk_size
        self.min_chunk_size = min_chunk_size
        self.max_chunk_size = max_chunk_size
        self._transfer_times = deque(maxlen=20)
        self._last_adjustment = time.time()
        self._adjustment_interval = 2.0  # 調整間隔（秒）

    def record_transfer_time(self, data_size: int, transfer_time: float):
        """転送時間を記録"""
        throughput = data_size / transfer_time if transfer_time > 0 else 0
        self._transfer_times.append(throughput)
        
        # 定期的にチャンクサイズを調整
        if (time.time() - self._last_adjustment > self._adjustment_interval and 
            len(self._transfer_times) >= 10):
            self._adjust_chunk_size()

    def _adjust_chunk_size(self):
        """スループットに基づいてチャンクサイズを調整"""
        if len(self._transfer_times) < 10:
            return
            
        recent_throughput = sum(list(self._transfer_times)[-10:]) / 10
        older_throughput = sum(list(self._transfer_times)[-20:-10]) / 10 if len(self._transfer_times) >= 20 else recent_throughput
        
        # スループットが向上している場合はチャンクサイズを増加
        if recent_throughput > older_throughput * 1.05:
            self.current_chunk_size = min(
                self.max_chunk_size,
                int(self.current_chunk_size * 1.2)
            )
        # スループットが低下している場合はチャンクサイズを減少
        elif recent_throughput < older_throughput * 0.95:
            self.current_chunk_size = max(
                self.min_chunk_size,
                int(self.current_chunk_size * 0.8)
            )
        
        self._last_adjustment = time.time()

    def get_chunk_size(self) -> int:
        """現在の最適チャンクサイズ取得"""
        return self.current_chunk_size


class ColorConverter:
    """
    高速カラー変換ユーティリティ
    様々な色空間変換をルックアップテーブルで高速化
    """
    
    def __init__(self):
        self._rgb565_cache = LookupTableCache.get_instance('rgb565')
        self._gamma_cache = LookupTableCache.get_instance('gamma')

    def rgb_to_rgb565_fast(self, rgb_array: np.ndarray) -> bytes:
        """NumPy配列からRGB565への高速変換"""
        r_table = self._rgb565_cache.get_table('r_shift')
        g_table = self._rgb565_cache.get_table('g_shift')
        b_table = self._rgb565_cache.get_table('b_shift')
        
        r_vals = r_table[rgb_array[:, :, 0]]
        g_vals = g_table[rgb_array[:, :, 1]]
        b_vals = b_table[rgb_array[:, :, 2]]
        
        rgb565 = r_vals | g_vals | b_vals
        return rgb565.astype('>u2').tobytes()

    def apply_gamma_correction(self, rgb_array: np.ndarray, gamma: float = 2.2) -> np.ndarray:
        """ガンマ補正適用"""
        gamma_table = self._gamma_cache.get_table('gamma_table', gamma=gamma)
        return gamma_table[rgb_array]


# 使用例とファクトリー関数
def create_embedded_optimizer(buffer_pool_size: int = 8,
                            max_dirty_regions: int = 8) -> dict:
    """
    組み込みシステム向けの最適化オブジェクト一式を作成
    
    :param buffer_pool_size: メモリプール最大サイズ
    :param max_dirty_regions: ダーティ領域最大数
    :return: 最適化オブジェクト辞書
    """
    return {
        'memory_pool': MemoryPool(max_pools=buffer_pool_size),
        'region_optimizer': RegionOptimizer(),
        'performance_monitor': PerformanceMonitor(),
        'adaptive_chunking': AdaptiveChunking(),
        'color_converter': ColorConverter()
    }
