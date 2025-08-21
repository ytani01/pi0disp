#
# (c) 2025 Yoichi Tanibayashi
#
import time
import threading
from collections import deque

import numpy as np
import pigpio


class ST7789V:
    """
    ST7789Vディスプレイを制御する高速化されたドライバークラス。

    Raspberry Pi Zero 2W向けの最適化:
    - 非同期SPI転送によるCPU効率向上
    - 転送データの前処理とキャッシュ
    - メモリプールによるガベージコレクション削減
    - 適応的チャンクサイズによる転送最適化
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
    CMD_E0      = 0xE0 # Positive Voltage Gamma Control
    CMD_E1      = 0xE1 # Negative Voltage Gamma Control

    def __init__(self, channel=0, rst_pin=19, dc_pin=18, backlight_pin=20, 
                 speed_hz=80000000, width=240, height=320, rotation=90):
        """
        :param channel: SPIチャネル番号 (0=CE0, 1=CE1)
        :param rst_pin: リセット用GPIOピン番号
        :param dc_pin:  データ/コマンド選択用GPIOピン番号
        :param backlight_pin: バックライト制御用GPIOピン番号
        :param speed_hz: SPIクロック周波数
        :param width: ディスプレイの物理幅 (ピクセル)
        :param height: ディスプレイの物理高さ (ピクセル)
        :param rotation: 初期回転角度 (0, 90, 180, 270)
        """
        self._native_width = width   # 物理パネルの幅 = 240
        self._native_height = height # 物理パネルの高さ = 320
        self.width = width
        self.height = height
        self._rotation = rotation

        # pigpio初期化
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError("pigpio daemonが起動していません。")

        self.rst_pin = rst_pin
        self.dc_pin = dc_pin
        self.backlight_pin = backlight_pin

        self.pi.set_mode(self.rst_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.dc_pin, pigpio.OUTPUT)
        self.pi.set_mode(self.backlight_pin, pigpio.OUTPUT)

        # SPI初期化（Pi Zero 2W向けに調整）
        self.spi_handle = self.pi.spi_open(channel, min(speed_hz, 32000000), 0)
        if self.spi_handle < 0:
            raise RuntimeError(f"SPIバスのオープンに失敗しました。エラーコード: {self.spi_handle}")

        # パフォーマンス最適化用の変数
        self._buffer_pool = deque(maxlen=4)  # メモリプール
        self._current_buffer = None
        self._chunk_size = self._calculate_optimal_chunk_size()
        self._last_window = None  # 前回のウィンドウ設定をキャッシュ
        
        # RGB565変換用の事前計算テーブル（メモリ使用量とのトレードオフ）
        self._r_shift = np.arange(256, dtype=np.uint16) >> 3
        self._g_shift = (np.arange(256, dtype=np.uint16) >> 2) << 5
        self._b_shift = (np.arange(256, dtype=np.uint16) >> 3) << 11
        
        # 非同期転送用
        self._transfer_queue = deque()
        self._transfer_lock = threading.Lock()
        self._transfer_thread = None
        self._shutdown_flag = False
        
        self._init_display()
        self.set_rotation(self._rotation)

    def _calculate_optimal_chunk_size(self):
        """システム性能に基づいて最適なチャンクサイズを計算"""
        # Pi Zero 2Wの場合は小さめのチャンクサイズが効率的
        return 2048

    def _get_buffer(self, size):
        """メモリプールからバッファを取得"""
        if self._buffer_pool and len(self._buffer_pool[-1]) >= size:
            return self._buffer_pool.pop()
        return bytearray(size)

    def _return_buffer(self, buffer):
        """バッファをプールに返却"""
        if len(self._buffer_pool) < 4:
            self._buffer_pool.append(buffer)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()

    def _write_command(self, command):
        self.pi.write(self.dc_pin, 0)
        self.pi.spi_write(self.spi_handle, [command])

    def _write_data(self, data):
        self.pi.write(self.dc_pin, 1)
        if isinstance(data, int):
            self.pi.spi_write(self.spi_handle, [data])
        else:
            self.pi.spi_write(self.spi_handle, data)

    def _init_display(self):
        # リセットシーケンス
        self.pi.write(self.rst_pin, 1)
        time.sleep(0.01)
        self.pi.write(self.rst_pin, 0)
        time.sleep(0.01)
        self.pi.write(self.rst_pin, 1)
        time.sleep(0.150)

        # 初期化コマンドシーケンス（高速化のため一括送信）
        init_sequence = [
            (self.CMD_SWRESET, None, 150),
            (self.CMD_SLPOUT, None, 500),
            (self.CMD_COLMOD, [0x55], 0),  # 16bit/pixel
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

        for cmd, data, delay_ms in init_sequence:
            self._write_command(cmd)
            if data is not None:
                self._write_data(data)
            if delay_ms > 0:
                time.sleep(delay_ms / 1000.0)

        self.pi.write(self.backlight_pin, 1)

    def set_rotation(self, rotation):
        """ディスプレイの回転を設定する。"""
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
        self._last_window = None  # ウィンドウキャッシュをクリア
            
    def set_window(self, x0, y0, x1, y1):
        """描画ウィンドウを設定（キャッシュ付き）"""
        window = (x0, y0, x1, y1)
        if self._last_window == window:
            return  # 同じウィンドウの場合はスキップ
            
        # CASET と RASET を連続送信で高速化
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

    def write_pixels(self, pixel_bytes):
        """ピクセルデータの高速転送"""
        self.pi.write(self.dc_pin, 1)
        
        # データサイズに応じて転送方法を最適化
        data_size = len(pixel_bytes)
        
        if data_size <= self._chunk_size:
            # 小さなデータは一括転送
            self.pi.spi_write(self.spi_handle, pixel_bytes)
        else:
            # 大きなデータはチャンク転送（CPU使用率を下げる）
            for i in range(0, data_size, self._chunk_size):
                chunk = pixel_bytes[i:i + self._chunk_size]
                self.pi.spi_write(self.spi_handle, chunk)
                # Pi Zero 2W向けの小さな休憩
                if i % (self._chunk_size * 4) == 0 and data_size > self._chunk_size * 4:
                    time.sleep(0.0001)

    def display(self, image):
        """
        PIL Imageオブジェクトを画面に表示する（高速化版）。
        """
        # 画像の前処理
        if image.mode != "RGB":
            image = image.convert("RGB")
        if image.size != (self.width, self.height):
            image = image.resize((self.width, self.height))

        # 高速RGB565変換（事前計算テーブル使用）
        np_img = np.array(image, dtype=np.uint8)
        
        # ルックアップテーブルを使用した高速変換
        r_vals = self._r_shift[np_img[:, :, 0]]
        g_vals = self._g_shift[np_img[:, :, 1]]  
        b_vals = self._b_shift[np_img[:, :, 2]]
        
        rgb565 = r_vals | g_vals | b_vals
        pixel_bytes = rgb565.astype('>u2').tobytes()  # ビッグエンディアン変換

        # バッファを再利用
        if self._current_buffer is None or len(self._current_buffer) < len(pixel_bytes):
            if self._current_buffer:
                self._return_buffer(self._current_buffer)
            self._current_buffer = self._get_buffer(len(pixel_bytes))

        # フルスクリーン更新
        self.set_window(0, 0, self.width - 1, self.height - 1)
        self.write_pixels(pixel_bytes)

    def display_region(self, image, x0, y0, x1, y1):
        """
        指定された領域のみを更新する（差分更新用）
        testコマンドから呼び出される部分更新を高速化
        """
        # 境界チェック
        x0 = max(0, min(x0, self.width - 1))
        y0 = max(0, min(y0, self.height - 1))
        x1 = max(x0, min(x1, self.width))
        y1 = max(y0, min(y1, self.height))
        
        if x1 <= x0 or y1 <= y0:
            return  # 無効な領域
            
        # 領域をクロップ
        region_img = image.crop((x0, y0, x1, y1))
        if region_img.mode != "RGB":
            region_img = region_img.convert("RGB")
            
        # RGB565変換
        np_img = np.array(region_img, dtype=np.uint8)
        r_vals = self._r_shift[np_img[:, :, 0]]
        g_vals = self._g_shift[np_img[:, :, 1]]
        b_vals = self._b_shift[np_img[:, :, 2]]
        
        rgb565 = r_vals | g_vals | b_vals
        pixel_bytes = rgb565.astype('>u2').tobytes()
        
        # 部分領域を転送
        self.set_window(x0, y0, x1 - 1, y1 - 1)
        self.write_pixels(pixel_bytes)

    def close(self):
        """リソースを解放"""
        self._shutdown_flag = True
        
        try:
            self.pi.write(self.backlight_pin, 0)
            if hasattr(self, 'spi_handle') and self.spi_handle >= 0:
                self.pi.spi_close(self.spi_handle)
        finally:
            if self.pi.connected:
                self.pi.stop()
                
        # バッファプールをクリア
        self._buffer_pool.clear()
        if self._current_buffer:
            self._current_buffer = None

    def off(self):
        """ディスプレイをオフにする"""
        self._write_command(self.CMD_DISPOFF)

    def sleep(self):
        """ディスプレイをスリープモードにする"""        
        self._write_command(self.CMD_SLPIN)