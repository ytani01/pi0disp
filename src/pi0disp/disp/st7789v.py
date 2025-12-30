#
# (c) 2025 Yoichi Tanibayashi
#
"""
ST7789V Display Driver for Raspberry Pi.

This module provides a high-performance driver for ST7789V-based displays,
optimized for Raspberry Pi environments. It leverages the `performance_core`
module to achieve high frame rates with low CPU usage.
"""

import time
from typing import Optional, Tuple

import numpy as np
from PIL import Image

from ..utils.mylogger import get_logger
from ..utils.performance_core import create_optimizer_pack
from .disp_base import DispSize
from .disp_spi import DispSpi, SpiPins


class ST7789V(DispSpi):
    """
    ST7789Vコントローラを搭載したSPIディスプレイ用の最適化されたドライバ。
    高速な描画処理とRaspberry Pi環境への最適化が施されている。
    """

    CMD = {
        "SWRESET": 0x01,
        "SLPIN": 0x10,
        "SLPOUT": 0x11,
        "NORON": 0x13,
        "INVOFF": 0x20,
        "INVON": 0x21,
        "DISPOFF": 0x28,
        "DISPON": 0x29,
        "CASET": 0x2A,
        "RASET": 0x2B,
        "RAMWR": 0x2C,
        "MADCTL": 0x36,
        "COLMOD": 0x3A,
    }

    def __init__(
        self,
        bl_at_close: bool = False,
        pin: SpiPins | None = None,
        brightness: int = 255,
        channel: int = 0,
        speed_hz: int | None = None,
        size: DispSize | None = None,
        rotation: int | None = None,
        invert: bool = True,
        bgr: bool = True,
        debug=False,
    ):
        """
        ST7789Vディスプレイドライバを初期化する。

        パラメータ:
            bl_at_close (bool): `close()`メソッド呼び出し時にバックライトをオフにするかどうか。
            pin (SpiPins | None): SPIピン構成 (RST, DC, CS, BLのGPIO番号)。
                                  指定しない場合、設定ファイルまたはデフォルト値を使用。
            brightness (int): 初期バックライトの明るさ (0-255)。
            channel (int): pigpioによって使用されるSPIチャンネル (0または1)。
            speed_hz (int | None): SPI通信速度 (Hz)。
                                   指定しない場合、設定ファイルまたはデフォルト値を使用。
            size (DispSize | None): ディスプレイの物理サイズ (幅, 高さ)。
            rotation (int | None): ディスプレイの初期回転角度 (0, 90, 180, 270)。
            invert (bool): ディスプレイの色を反転するかどうか。`True`で反転を有効。
            bgr (bool): BGRカラー順序を使用するかどうか。`True`でBGR、`False`でRGB。
            debug (bool): デバッグモードを有効にするか。
        """
        super().__init__(
            bl_at_close=bl_at_close,
            pin=pin,
            brightness=brightness,
            channel=channel,
            speed_hz=speed_hz,
            size=size,
            rotation=rotation,
            debug=debug,
        )
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("")
        self._invert = invert
        self._bgr = bgr

        # Initialize the optimizer pack
        self._optimizers = create_optimizer_pack()
        self._last_window: Optional[Tuple[int, int, int, int]] = None

        self.set_rotation(self._rotation)
        self.init_display()

    def init_display(self):
        """
        ST7789Vのハードウェア初期化シーケンスを実行する。

        ディスプレイの電源投入、カラーモード設定、表示オンなどを行う。
        """
        super().init_display()
        self.__log.debug("")

        # Initialization sequence
        # self._write_command(self.CMD["SWRESET"]) # ソフトウェアリセットは親クラスで実行
        # time.sleep(0.150)
        self._write_command(self.CMD["SLPOUT"])
        time.sleep(0.120)
        self._write_command(self.CMD["COLMOD"])
        self._write_data(0x55)  # 16 bits per pixel (RGB565)
        if self._invert:
            self._write_command(self.CMD["INVON"])
        else:
            self._write_command(self.CMD["INVOFF"])
        self._write_command(self.CMD["NORON"])
        self._write_command(self.CMD["DISPON"])
        time.sleep(0.1)

    def set_rotation(self, rotation: int):
        """
        ディスプレイの回転を設定する。

        回転角度に応じてMADCTLレジスタを更新し、表示方向とカラー順序を制御する。

        パラメータ:
            rotation (int): 回転角度 (0, 90, 180, 270)。
        """
        self.rotation = rotation
        self.__log.debug("%s", self.__class__.__name__)

        madctl_values = {0: 0x00, 90: 0x60, 180: 0xC0, 270: 0xA0}
        if rotation not in madctl_values:
            raise ValueError("Rotation must be 0, 90, 180, or 270.")

        if hasattr(self, "spi_handle"):
            madctl = madctl_values[rotation]
            if self._bgr:
                madctl |= 0x08  # Set BGR bit (bit 3)
            self._write_command(self.CMD["MADCTL"])
            self._write_data(madctl)

        self._last_window = None  # Invalidate window cache

    def set_window(self, x0: int, y0: int, x1: int, y1: int):
        """
        ディスプレイ上のアクティブな描画ウィンドウを設定する。

        この範囲内にのみピクセルデータが書き込まれる。

        パラメータ:
            x0 (int): ウィンドウの左上X座標。
            y0 (int): ウィンドウの左上Y座標。
            x1 (int): ウィンドウの右下X座標。
            y1 (int): ウィンドウの右下Y座標。
        """
        window = (x0, y0, x1, y1)
        if self._last_window == window:
            return

        self._write_command(self.CMD["CASET"])
        self._write_data([x0 >> 8, x0 & 0xFF, x1 >> 8, x1 & 0xFF])
        self._write_command(self.CMD["RASET"])
        self._write_data([y0 >> 8, y0 & 0xFF, y1 >> 8, y1 & 0xFF])
        self._write_command(self.CMD["RAMWR"])

        self._last_window = window

    def write_pixels(self, pixel_bytes: bytes):
        """
        現在のウィンドウにピクセルデータの生バッファを書き込む。

        データは `set_window` で設定された領域に書き込まれる。

        パラメータ:
            pixel_bytes (bytes): 書き込むピクセルデータ (RGB565フォーマット)。
        """
        chunk_size = self._optimizers["adaptive_chunking"].get_chunk_size()
        data_len = len(pixel_bytes)

        self.pi.write(self.pin.dc, 1)  # D/CピンをHighに設定（データモード）

        if data_len <= chunk_size:
            self.pi.spi_write(self.spi_handle, pixel_bytes)
        else:
            for i in range(0, data_len, chunk_size):
                self.pi.spi_write(
                    self.spi_handle, pixel_bytes[i : i + chunk_size]
                )

    def display(self, image: Image.Image):
        """
        画面全体にPIL Imageオブジェクトを表示する。

        パラメータ:
            image (Image.Image): 表示するPIL Imageオブジェクト。
        """
        super().display(image)
        self.__log.debug("%s", self.__class__.__name__)

        pixel_bytes = self._optimizers["color_converter"].rgb_to_rgb565_bytes(
            np.array(image)
        )

        self.set_window(0, 0, self.size.width - 1, self.size.height - 1)
        self.write_pixels(pixel_bytes)

    def display_region(
        self, image: Image.Image, x0: int, y0: int, x1: int, y1: int
    ):
        """
        指定された領域内にPIL Imageオブジェクトの一部を表示する。

        パラメータ:
            image (Image.Image): 表示するPIL Imageオブジェクト。
            x0 (int): 描画領域の左上X座標。
            y0 (int): 描画領域の左上Y座標。
            x1 (int): 描画領域の右下X座標。
            y1 (int): 描画領域の右下Y座標。
        """
        # Clamp region to be within display boundaries
        region = self._optimizers["region_optimizer"].clamp_region(
            (x0, y0, x1, y1), self.size.width, self.size.height
        )

        if region[2] <= region[0] or region[3] <= region[1]:
            return  # Skip zero- or negative-sized regions

        # Crop the image to the specified region and convert to pixel data
        region_img = image.crop(region)
        pixel_bytes = self._optimizers["color_converter"].rgb_to_rgb565_bytes(
            np.array(region_img)
        )

        # Set window and write data
        self.set_window(region[0], region[1], region[2] - 1, region[3] - 1)
        self.write_pixels(pixel_bytes)

    def close(self, bl_switch: bool | None = None):
        """
        リソースをクリーンアップし、ディスプレイをスリープ状態にする。

        SPI接続を閉じ、DISPOFF/SLPINコマンドを送信する。

        パラメータ:
            bl_switch (bool | None): バックライトの最終状態を明示的に指定する。
                                    `None`の場合、オブジェクト生成時の`bl_at_close`設定に従う。
        """
        self.__log.debug("ディスプレイをスリープさせ、リソースをクリーンアップします。")
        if hasattr(self, "spi_handle") and self.pi.connected:
            self._write_command(self.CMD["INVOFF"])
            self._write_command(self.CMD["DISPOFF"])
            self._write_command(self.CMD["SLPIN"])
            time.sleep(0.01)  # コマンド実行のための時間を与える

        super().close(bl_switch)

    def dispoff(self):
        """
        ディスプレイをオフにする (DISPOFFコマンド)。

        バックライトもオフにする。
        """
        self._write_command(self.CMD["DISPOFF"])
        self.set_backlight(False)

    def sleep(self):
        """
        ディスプレイをスリープモードにする (SLPINコマンド)。

        バックライトもオフにする。
        """
        self._write_command(self.CMD["SLPIN"])
        self.set_backlight(False)

    def wake(self):
        """
        ディスプレイをスリープモードから起動する (SLPOUTコマンド)。

        バックライトもオンにする。
        """
        self._write_command(self.CMD["SLPOUT"])
        self.set_backlight(True)
