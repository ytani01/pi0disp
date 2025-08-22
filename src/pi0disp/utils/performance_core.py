# -*- coding: utf-8 -*-
"""
performance_core.py - A generic module for performance optimization.

This module provides a set of reusable classes designed for performance
optimization in resource-constrained environments like the Raspberry Pi Zero 2W.
Each class focuses on a specific optimization technique.
"""
import time
import threading
from collections import deque
from typing import List, Tuple, Callable, Any, Dict

import numpy as np

# --- Optimization Classes ---

class MemoryPool:
    """
    Manages pools of reusable buffers to reduce garbage collection overhead
    by recycling frequently allocated memory blocks.
    """
    def __init__(self, max_pools: int = 8, buffer_factory: Callable[[int], Any] = bytearray):
        """
        Initializes the memory pool.

        Args:
            max_pools (int): The maximum number of buffers to store per size.
            buffer_factory (Callable): A function to create new buffers, e.g., bytearray.
        """
        self._pools: Dict[int, deque] = {}  # Pools categorized by buffer size
        self._max_pools = max_pools
        self._buffer_factory = buffer_factory
        self._lock = threading.Lock()
        self._stats = {'hits': 0, 'misses': 0, 'created': 0}

    def get_buffer(self, size: int) -> Any:
        """
        Retrieves a buffer of at least the specified size from the pool.
        If no suitable buffer is found, a new one is created.

        Args:
            size (int): The required minimum buffer size.

        Returns:
            A buffer object.
        """
        with self._lock:
            # Find the smallest available buffer that is large enough
            for pool_size in sorted(self._pools.keys()):
                if pool_size >= size and self._pools[pool_size]:
                    self._stats['hits'] += 1
                    return self._pools[pool_size].pop()
            
            # If no suitable buffer is found, create a new one
            self._stats['misses'] += 1
            self._stats['created'] += 1
            return self._buffer_factory(size)

    def return_buffer(self, buffer: Any):
        """
        Returns a buffer to the pool for future reuse.

        Args:
            buffer: The buffer object to return.
        """
        size = len(buffer)
        with self._lock:
            if size not in self._pools:
                self._pools[size] = deque(maxlen=self._max_pools)
            
            if len(self._pools[size]) < self._max_pools:
                self._pools[size].append(buffer)

    def get_stats(self) -> dict:
        """Returns statistics about pool usage (hits, misses, etc.)."""
        with self._lock:
            return self._stats.copy()

    def clear(self):
        """Empties all pools and resets statistics."""
        with self._lock:
            self._pools.clear()
            self._stats = {'hits': 0, 'misses': 0, 'created': 0}


class LookupTableCache:
    """
    A singleton cache for pre-calculated lookup tables (LUTs).
    Used to accelerate expensive computations like color conversion or gamma correction.
    """
    _instances: Dict[str, 'LookupTableCache'] = {}
    _lock = threading.Lock()

    @classmethod
    def get_instance(cls, table_type: str) -> 'LookupTableCache':
        """Provides access to the singleton instance for a given table type."""
        with cls._lock:
            if table_type not in cls._instances:
                cls._instances[table_type] = cls(table_type)
            return cls._instances[table_type]

    def __init__(self, table_type: str):
        self.table_type = table_type
        self._tables: Dict[str, np.ndarray] = {}
        self._generators: Dict[str, Callable[..., Dict[str, np.ndarray]]] = {
            'rgb565': self._generate_rgb565_tables,
            'gamma': self._generate_gamma_tables,
        }

    def _generate_rgb565_tables(self) -> Dict[str, np.ndarray]:
        """Generates LUTs for fast RGB to RGB565 conversion."""
        return {
            'r_shift': (np.arange(256, dtype=np.uint16) >> 3) << 11,
            'g_shift': (np.arange(256, dtype=np.uint16) >> 2) << 5,
            'b_shift': (np.arange(256, dtype=np.uint16) >> 3),
        }

    def _generate_gamma_tables(self, gamma: float = 2.2) -> Dict[str, np.ndarray]:
        """Generates a LUT for gamma correction."""
        table = np.array([
            int(255 * ((i / 255.0) ** gamma)) for i in range(256)
        ], dtype=np.uint8)
        return {'gamma_table': table}

    def get_table(self, table_name: str, **kwargs: Any) -> np.ndarray:
        """
        Retrieves a table, generating it if it doesn't exist in the cache.
        
        Args:
            table_name (str): The name of the table to retrieve.
            **kwargs: Parameters for the table generation function (e.g., gamma=2.2).

        Returns:
            The requested lookup table (typically a NumPy array).
        """
        cache_key = f"{table_name}_{hash(str(sorted(kwargs.items())))}"
        if cache_key not in self._tables:
            if self.table_type not in self._generators:
                raise ValueError(f"Unknown table type: {self.table_type}")
            
            generated = self._generators[self.table_type](**kwargs)
            if table_name not in generated:
                raise KeyError(f"Table '{table_name}' not found for type '{self.table_type}'")
            
            self._tables[cache_key] = generated[table_name]
        
        return self._tables[cache_key]


class RegionOptimizer:
    """
    Optimizes lists of rectangular regions ("dirty regions") by merging
    overlapping or nearby rectangles to reduce the number of drawing operations.
    """
    @staticmethod
    def merge_regions(regions: List[Tuple[int, int, int, int]], 
                     max_regions: int = 8, 
                     merge_threshold: int = 50) -> List[Tuple[int, int, int, int]]:
        """
        Merges a list of regions into a smaller, optimized list.

        Args:
            regions: A list of tuples, where each tuple is (x0, y0, x1, y1).
            max_regions: The maximum number of regions to return.
            merge_threshold: The maximum distance between regions to be considered for merging.

        Returns:
            An optimized list of merged regions.
        """
        if len(regions) <= 1:
            return regions

        valid_regions = [r for r in regions if r and r[2] > r[0] and r[3] > r[1]]
        if not valid_regions:
            return []

        # Start with the smallest regions to encourage merging
        merged: List[Tuple[int, int, int, int]] = []
        sorted_regions = sorted(valid_regions, key=lambda r: (r[2] - r[0]) * (r[3] - r[1]))

        while sorted_regions:
            current = sorted_regions.pop(0)
            was_merged = False
            for i, existing in enumerate(merged):
                if RegionOptimizer._should_merge(current, existing, merge_threshold):
                    merged[i] = RegionOptimizer._merge_two(current, existing)
                    was_merged = True
                    break
            if not was_merged:
                merged.append(current)

        # If we still have too many regions, perform more aggressive merging
        while len(merged) > max_regions:
            # Find the pair of regions that results in the smallest new area when merged
            min_area_increase = float('inf')
            best_pair_to_merge = (0, 1)
            for i in range(len(merged)):
                for j in range(i + 1, len(merged)):
                    r1, r2 = merged[i], merged[j]
                    merged_bbox = RegionOptimizer._merge_two(r1, r2)
                    area_increase = ((merged_bbox[2] - merged_bbox[0]) * (merged_bbox[3] - merged_bbox[1])) - \
                                    ((r1[2] - r1[0]) * (r1[3] - r1[1])) - \
                                    ((r2[2] - r2[0]) * (r2[3] - r2[1]))
                    if area_increase < min_area_increase:
                        min_area_increase = area_increase
                        best_pair_to_merge = (i, j)
            
            i, j = sorted(best_pair_to_merge, reverse=True)
            merged_region = RegionOptimizer._merge_two(merged[i], merged[j])
            merged.pop(j)
            merged.pop(i)
            merged.append(merged_region)

        return merged

    @staticmethod
    def _should_merge(r1: Tuple[int, int, int, int], r2: Tuple[int, int, int, int], threshold: int) -> bool:
        """Determines if two regions are close enough to be merged."""
        # Check for overlap or proximity within the threshold
        x_overlap = (r1[0] <= r2[2] + threshold) and (r1[2] >= r2[0] - threshold)
        y_overlap = (r1[1] <= r2[3] + threshold) and (r1[3] >= r2[1] - threshold)
        return x_overlap and y_overlap

    @staticmethod
    def _merge_two(r1: Tuple[int, int, int, int], r2: Tuple[int, int, int, int]) -> Tuple[int, int, int, int]:
        """Merges two regions into their bounding box."""
        return (
            min(r1[0], r2[0]),
            min(r1[1], r2[1]),
            max(r1[2], r2[2]),
            max(r1[3], r2[3])
        )

    @staticmethod
    def clamp_region(region: Tuple[int, int, int, int], width: int, height: int) -> Tuple[int, int, int, int]:
        """Clamps a region's coordinates to be within screen boundaries."""
        return (
            max(0, region[0]),
            max(0, region[1]),
            min(width, region[2]),
            min(height, region[3])
        )


class PerformanceMonitor:
    """
    Tracks performance metrics like FPS and processing time.
    """
    def __init__(self, window_size: int = 60):
        """
        Args:
            window_size: The number of frames to average over for statistics.
        """
        self.window_size = window_size
        self._frame_times: deque[float] = deque(maxlen=window_size)
        self._process_times: deque[float] = deque(maxlen=window_size)
        self._last_frame_time = time.monotonic()

    def frame_start(self) -> float:
        """Marks the beginning of a new frame."""
        now = time.monotonic()
        delta = now - self._last_frame_time
        self._frame_times.append(delta)
        self._last_frame_time = now
        return now

    def frame_end(self, start_time: float):
        """Marks the end of a frame's processing."""
        self._process_times.append(time.monotonic() - start_time)

    def get_fps(self) -> float:
        """Calculates the current average frames per second."""
        if not self._frame_times:
            return 0.0
        return 1.0 / (sum(self._frame_times) / len(self._frame_times))

    def get_stats(self) -> dict:
        """Returns a dictionary of all current performance statistics."""
        return {
            'fps': self.get_fps(),
            'avg_process_time_ms': (sum(self._process_times) / len(self._process_times) * 1000) if self._process_times else 0,
        }


class AdaptiveChunking:
    """
    Dynamically adjusts data transfer chunk sizes based on performance to
    optimize throughput.
    """
    def __init__(self, initial_size: int = 4096, min_size: int = 1024, max_size: int = 16384):
        self.chunk_size = initial_size
        self.min_size = min_size
        self.max_size = max_size
        self._throughputs: deque[float] = deque(maxlen=20)
        self._last_adjustment = time.monotonic()

    def record_transfer(self, data_size: int, transfer_time: float):
        """Records a data transfer to adjust future chunk sizes."""
        if transfer_time > 0:
            self._throughputs.append(data_size / transfer_time)
        
        if time.monotonic() - self._last_adjustment > 1.0 and len(self._throughputs) >= 10:
            self._adjust_chunk_size()

    def _adjust_chunk_size(self):
        """Adjusts chunk size based on recent throughput."""
        if len(self._throughputs) < 10:
            return

        recent_avg = sum(list(self._throughputs)[-10:]) / 10
        older_avg = sum(list(self._throughputs)[:-10]) / 10 if len(self._throughputs) > 10 else recent_avg

        if recent_avg > older_avg * 1.05:  # Throughput is improving
            self.chunk_size = min(self.max_size, int(self.chunk_size * 1.2))
        elif recent_avg < older_avg * 0.95:  # Throughput is degrading
            self.chunk_size = max(self.min_size, int(self.chunk_size * 0.8))
        
        self._last_adjustment = time.monotonic()

    def get_chunk_size(self) -> int:
        """Returns the current optimal chunk size."""
        return self.chunk_size


class ColorConverter:
    """
    Provides fast color space conversion utilities using cached lookup tables.
    """
    def __init__(self):
        self._rgb565_cache = LookupTableCache.get_instance('rgb565')
        self._gamma_cache = LookupTableCache.get_instance('gamma')

    def rgb_to_rgb565_bytes(self, rgb_array: np.ndarray) -> bytes:
        """
        Converts an RGB NumPy array to a big-endian RGB565 byte string.

        Args:
            rgb_array: A NumPy array with shape (height, width, 3).

        Returns:
            A byte string containing the RGB565 pixel data.
        """
        r = self._rgb565_cache.get_table('r_shift')[rgb_array[:, :, 0]]
        g = self._rgb565_cache.get_table('g_shift')[rgb_array[:, :, 1]]
        b = self._rgb565_cache.get_table('b_shift')[rgb_array[:, :, 2]]
        
        rgb565 = r | g | b
        return rgb565.astype('>u2').tobytes()

    def apply_gamma(self, rgb_array: np.ndarray, gamma: float = 2.2) -> np.ndarray:
        """Applies gamma correction to an RGB NumPy array."""
        gamma_table = self._gamma_cache.get_table('gamma_table', gamma=gamma)
        return gamma_table[rgb_array]

# --- Factory Function ---

def create_optimizer_pack() -> dict:
    """
    Creates a standard dictionary of optimizer instances for convenience.

    Returns:
        A dictionary containing instances of the core optimization classes.
    """
    return {
        'memory_pool': MemoryPool(),
        'region_optimizer': RegionOptimizer(),
        'performance_monitor': PerformanceMonitor(),
        'adaptive_chunking': AdaptiveChunking(),
        'color_converter': ColorConverter(),
    }
