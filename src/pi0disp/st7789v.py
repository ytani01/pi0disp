#
# (c) 2025 Yoichi Tanibayashi
#
"""
ST7789V最適化ドライバ（モジュラー版）
performance_coreの汎用最適化機能を活用した高性能ディスプレイドライバ
"""
import time
from typing import Optional, Tuple, Union

import numpy as np
import pigpio
from PIL import Image

from .performance_core import (
    MemoryPool, RegionOptimizer, PerformanceMonitor,
    AdaptiveChunking, ColorConverter, create_embedded_optimizer
)


class ST7789V:
    """
    最適化されたST7789Vドライバクラス
    汎用パフォーマンス最適化モジュールを活用してリソース効率を最大化
    """
    # ST7789V コマンド定義
    CMD_NOP     = 0x00
    CMD_SWRESET = 0x01
    CMD_SLPIN   = 0x10
    CMD_SLPOUT  = 0x11
    CMD_NORON   = 0x13
    CMD_INVON   = 0x21
    CMD_DISPOFF = 0x28
    CMD_DISPON  = 0x29
    CMD_CASET   = 0x2A
    CMD_RASET   = 0x2B
    CMD_RAMWR   = 0x2C
    CMD_MADCTL  = 0x36
    CMD_COLMOD  = 0x3A
    CMD_E0      = 0xE0
    CMD_E1      = 0xE1

    def __init__(self, 
                 channel: int = 0, 
                 rst_pin: int = 19, 
                 dc_pin: int = 18, 
                 backlight_pin: int = 20,
                 speed_hz: int = 80000000, 
                 width: int = 240, 
                 height: int = 320, 
                 rotation: int = 90,
                 optimization_level: str = "balanced"):
        """
        最適化されたST7789Vドライバを初期化
        
        :param optimization_level: 最適化レベル ("low", "balanced", "high")
        """
        # 基本設定
        self._native_width = width
        self._native_height = height
        self.width = width
        self.height = height
        self._rotation = rotation
        
        # 最適化レベルに応じた設定
        self._optimization_config = self._get_optimization_config(optimization_level)
        
        # 汎用最適化オブジェクト群を初期化
        self._optimizers = create_embedded_optimizer(
            buffer_pool_size=self._optimization_config['buffer_pool_size'],
            max_dirty_regions=self._optimization_config['max_dirty_regions']
        )
        
        # pigpio初期化
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemonが起動していません。")

        self.rst_pin = rst_pin
        self.dc_pin = dc_pin
        self.backlight_pin = backlight_pin

        # GPIO設定
        for pin in [self.rst_pin, self.dc_pin, self.backlight_pin]:
            self.pi.set_mode(pin, pigpio.OUTPUT)

        # SPI初期化（最適化レベルに応じて調整）
        max_speed = min(speed_hz, self._optimization_config['max_spi_speed'])
        self.spi_handle = self.pi.spi_open(channel, max_speed, 0)
        if self.spi_handle < 0:
            raise RuntimeError(f"SPIバスのオープンに失敗: {self.spi_handle}")

        # 最適化関連の初期化
        self._last_window = None
        self._frame_buffer_cache = None
        
        # ディスプレイ初期化
        self._init_display()
        self.set_rotation(self._rotation)

    def _get_optimization_config(self, level: str) -> dict:
        """最適化レベルに応じた設定を取得"""
        configs = {
            "low": {
                "buffer_pool_size": 4,
                "max_dirty_regions": 4,
                "max_spi_speed": 16000000,
                "enable_adaptive_chunking": False,
                "enable_performance_monitoring": False
            },
            "balanced": {
                "buffer_pool_size": 8,
                "max_dirty_regions": 6,
                "max_spi_speed": 32000000,
                "enable_adaptive_chunking": True,
                "enable_performance_monitoring": True
            },
            "high": {
                "buffer_pool_size": 16,
                "max_dirty_regions": 8,
                "max_spi_speed": 80000000,
                "enable_adaptive_chunking": True,
                "enable_performance_monitoring": True
            }
        }
        return configs.get(level, configs["balanced"])

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _write_command(self, command: int):
        """コマンド送信"""
        self.pi.write(self.dc_pin, 0)
        self.pi.spi_write(self.spi_handle, [command])

    def _write_data(self, data: Union[int, bytes, list]):
        """データ送信"""
        self.pi.write(self.dc_pin, 1)
        if isinstance(data, int):
            self.pi.spi_write(self.spi_handle, [data])
        else:
            self.pi.spi_write(self.spi_handle, data)

    def _init_display(self):
        """ディスプレイ初期化シーケンス"""
        # リセット処理
        self.pi.write(self.rst_pin, 1)
        time.sleep(0.01)
        self.pi.write(self.rst_pin, 0)
        time.sleep(0.01)
        self.pi.write(self.rst_pin, 1)
        time.sleep(0.150)

        # 最適化された初期化シーケンス
        init_commands = [
            (self.CMD_SWRESET, None, 150),
            (self.CMD_SLPOUT, None, 500),
            (self.CMD_COLMOD, [0x55], 0),
            (0xB2, [0x0C, 0x0C, 0x00, 0x33, 0x33], 0),
            (0xB7, [0x35], 0),
            (0xBB, [0x19], 0),
            (0xC0, [0x2C], 0),
            (0xC2, [0x01, 0xFF], 0),
            (0xC3, [0x11], 0),
            (0xC4, [0x20], 0),
            (0xC6, [0x0F], 0),
            (0xD0, [0xA4, 0xA1], 0),
            (self.CMD_E0, [0xD0, 0x00, 0x02, 0x07, 0x0A, 0x28, 0x32, 0x44,
                           0x42, 0x06, 0x0E, 0x12, 0x14, 0x17, 0x00], 0),
            (self.CMD_E1, [0xD0, 0x00, 0x02, 0x07, 0x0A, 0x28, 0x31, 0x54,
                           0x47, 0x0E, 0x1C, 0x17, 0x1B, 0x1B, 0x00], 0),
            (self.CMD_INVON, None, 0),
            (self.CMD_DISPON, None, 100)
        ]

        for cmd, data, delay_ms in init_commands:
            self._write_command(cmd)
            if data is not None:
                self._write_data(data)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

        self.pi.write(self.backlight_pin, 1)

    def set_rotation(self, rotation: int):
        """回転設定"""
        madctl_values = {0: 0x00, 90: 0x60, 180: 0xC0, 270: 0xA0}
        if rotation not in madctl_values:
            raise ValueError("Rotation must be 0, 90, 180, or 270.")

        self._write_command(self.CMD_MADCTL)
        self._write_data(madctl_values[rotation])

        if rotation in (90, 270):
            self.width, self.height = self._native_height, self._native_width
        else:
            self.width, self.height = self._native_width, self._native_height

        self._rotation = rotation
        self._last_window = None

    def set_window(self, x0: int, y0: int, x1: int, y1: int):
        """描画ウィンドウ設定（キャッシュ機能付き）"""
        window = (x0, y0, x1, y1)
        if self._last_window == window:
            return  # 同じウィンドウの場合はスキップ

        # CASET と RASET を連続送信
        self.pi.write(self.dc_pin, 0)
        self.pi.spi_write(self.spi_handle, [self.CMD_CASET])
        self.pi.write(self.dc_pin, 1)
        self.pi.spi_write(self.spi_handle, [x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])

        self.pi.write(self.dc_pin, 0)
        self.pi.spi_write(self.spi_handle, [self.CMD_RASET])
        self.pi.write(self.dc_pin, 1)
        self.pi.spi_write(self.spi_handle, [y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])

        self.pi.write(self.dc_pin, 0)
        self.pi.spi_write(self.spi_handle, [self.CMD_RAMWR])

        self._last_window = window

    def write_pixels(self, pixel_bytes: bytes):
        """
        ピクセルデータの最適化転送
        適応的チャンクサイズとパフォーマンス監視を使用
        """
        self.pi.write(self.dc_pin, 1)
        
        # パフォーマンス監視開始
        if self._optimization_config['enable_performance_monitoring']:
            start_time = self._optimizers['performance_monitor'].frame_start()
        
        # 適応的チャンクサイズを取得
        if self._optimization_config['enable_adaptive_chunking']:
            chunk_size = self._optimizers['adaptive_chunking'].get_chunk_size()
        else:
            chunk_size = 4096
        
        data_size = len(pixel_bytes)
        transfer_start = time.time()
        
        if data_size <= chunk_size:
            # 小データは一括転送
            self.pi.spi_write(self.spi_handle, pixel_bytes)
        else:
            # チャンク転送
            for i in range(0, data_size, chunk_size):
                chunk = pixel_bytes[i:i + chunk_size]
                self.pi.spi_write(self.spi_handle, chunk)
                
                # CPU負荷分散（大きなデータの場合）
                if i % (chunk_size * 4) == 0 and data_size > chunk_size * 4:
                    time.sleep(0.0001)
        
        # 転送時間を記録
        transfer_time = time.time() - transfer_start
        if self._optimization_config['enable_adaptive_chunking'] and transfer_time > 0:
            self._optimizers['adaptive_chunking'].record_transfer_time(data_size, transfer_time)
        
        # パフォーマンス監視終了
        if self._optimization_config['enable_performance_monitoring']:
            self._optimizers['performance_monitor'].frame_end(start_time)

    def display(self, image: Image.Image):
        """フルスクリーン表示（高速化版）"""
        # 画像の前処理
        if image.mode != "RGB":
            image = image.convert("RGB")
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))

        # RGB565変換（汎用カラーコンバータ使用）
        np_img = np.array(image, dtype=np.uint8)
        pixel_bytes = self._optimizers['color_converter'].rgb_to_rgb565_fast(np_img)

        # バッファキャッシュ
        if (self._frame_buffer_cache is None or 
            len(self._frame_buffer_cache) != len(pixel_bytes)):
            if self._frame_buffer_cache:
                self._optimizers['memory_pool'].return_buffer(
                    self._frame_buffer_cache, len(self._frame_buffer_cache)
                )
            self._frame_buffer_cache = self._optimizers['memory_pool'].get_buffer(
                len(pixel_bytes)
            )

        # フルスクリーン転送
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.write_pixels(pixel_bytes)

    def display_regions(self, image: Image.Image, 
                       dirty_regions: list,
                       optimize_regions: bool = True):
        """
        複数領域の最適化表示
        ダーティ領域を最適化してからまとめて転送
        """
        if not dirty_regions:
            return

        # 画像の前処理
        if image.mode != "RGB":
            image = image.convert("RGB")

        # 領域最適化
        if optimize_regions:
            optimized_regions = self._optimizers['region_optimizer'].merge_regions(
                dirty_regions,
                max_regions=self._optimization_config['max_dirty_regions']
            )
        else:
            optimized_regions = dirty_regions

        # 各最適化領域を転送
        for region in optimized_regions:
            x0, y0, x1, y1 = region
            
            # 境界チェック
            clamped_region = self._optimizers['region_optimizer'].clamp_region(
                region, self.width, self.height
            )
            
            if (clamped_region[2] <= clamped_region[0] or 
                clamped_region[3] <= clamped_region[1]):
                continue  # 無効な領域をスキップ

            # 領域を切り出してRGB565変換
            region_img = image.crop(clamped_region)
            np_img = np.array(region_img, dtype=np.uint8)
            pixel_bytes = self._optimizers['color_converter'].rgb_to_rgb565_fast(np_img)

            # 領域を転送
            self.set_window(
                clamped_region[0], clamped_region[1], 
                clamped_region[2] - 1, clamped_region[3] - 1
            )
            self.write_pixels(pixel_bytes)

    def display_region(self, image: Image.Image, x0: int, y0: int, x1: int, y1: int):
        """単一領域の高速表示"""
        self.display_regions(image, [(x0, y0, x1, y1)], optimize_regions=False)

    def get_performance_stats(self) -> dict:
        """パフォーマンス統計取得"""
        stats = {}
        
        if self._optimization_config['enable_performance_monitoring']:
            stats.update(self._optimizers['performance_monitor'].get_stats())
        
        if self._optimization_config['enable_adaptive_chunking']:
            stats['current_chunk_size'] = self._optimizers['adaptive_chunking'].get_chunk_size()
        
        # メモリプール統計
        stats['memory_pool'] = self._optimizers['memory_pool'].get_stats()
        
        return stats

    def reset_performance_stats(self):
        """パフォーマンス統計リセット"""
        if self._optimization_config['enable_performance_monitoring']:
            self._optimizers['performance_monitor'] = PerformanceMonitor()
        
        self._optimizers['memory_pool'].clear()

    def close(self):
        """リソース解放"""
        try:
            self.pi.write(self.backlight_pin, 0)
            if hasattr(self, 'spi_handle') and self.spi_handle >= 0:
                self.pi.spi_close(self.spi_handle)
        finally:
            if self.pi.connected:
                self.pi.stop()

        # 最適化リソースをクリア
        self._optimizers['memory_pool'].clear()
        if self._frame_buffer_cache:
            self._frame_buffer_cache = None

    def off(self):
        """ディスプレイオフ"""
        self._write_command(self.CMD_DISPOFF)

    def sleep(self):
        """スリープモード"""
        self._write_command(self.CMD_SLPIN)
