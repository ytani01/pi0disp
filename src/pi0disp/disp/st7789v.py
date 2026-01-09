#
# (c) 2025 Yoichi Tanibayashi
#
"""
ST7789V Display Driver for Raspberry Pi.
"""

import time
from typing import Optional

import numpy as np
from PIL import Image, ImageChops

from ..utils.mylogger import get_logger
from ..utils.performance_core import ColorConverter
from ..utils.utils import clamp_region
from .disp_base import DispSize
from .disp_spi import DispSpi, SpiPins


class ST7789V(DispSpi):
    """
    ST7789Vコントローラを搭載したSPIディスプレイ用の最適化されたドライバ。
    """

    _CMD = {
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

    CHUNK_SIZE = 4096  # Optimized for SPI throughput on Pi

    def __init__(
        self,
        pin: SpiPins | None = None,
        brightness: int = 255,
        channel: int = 0,
        speed_hz: int | None = None,
        size: DispSize | None = None,
        rotation: int | None = None,
        x_offset: int | None = None,
        y_offset: int | None = None,
        invert: bool | None = None,
        bgr: bool | None = None,
        debug=False,
    ):
        """
        ST7789Vディスプレイドライバを初期化する。
        """
        super().__init__(
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

        # invert configuration
        if invert is None:
            invert = self._conf.data.get("invert", True)
        self._invert = invert

        # bgr configuration
        if bgr is None:
            if "bgr" in self._conf.data:
                bgr = self._conf.data["bgr"]
            elif "rgb" in self._conf.data:
                bgr = not self._conf.data["rgb"]
            else:
                bgr = False
        self._bgr = bgr

        # Offsets
        if x_offset is None:
            x_offset = self._conf.data.get("x_offset", 0)
        if y_offset is None:
            y_offset = self._conf.data.get("y_offset", 0)
        self._x_offset = x_offset
        self._y_offset = y_offset
        self._mv = 0

        # Initialize core components
        self._color_converter = ColorConverter()
        self._last_image: Optional[Image.Image] = None

        self.init_display()
        self.set_rotation(self._rotation)

    def init_display(self):
        """ハードウェア初期化シーケンス"""
        super().init_display()
        self._write_command(self._CMD["SLPOUT"])
        time.sleep(0.120)
        self._write_command(self._CMD["COLMOD"])
        self._write_data(0x55)
        if self._invert:
            self._write_command(self._CMD["INVON"])
        else:
            self._write_command(self._CMD["INVOFF"])
        self._write_command(self._CMD["NORON"])
        self._write_command(self._CMD["DISPON"])
        time.sleep(0.1)

    def set_rotation(self, rotation: int):
        """ディスプレイの回転を設定する"""
        madctl_values = {
            self.NORTH: 0x00,
            self.EAST: 0x60,
            self.SOUTH: 0xC0,
            self.WEST: 0xA0,
        }
        if rotation not in madctl_values:
            raise ValueError("Rotation must be 0, 90, 180, or 270.")

        self.rotation = rotation
        if rotation in [self.EAST, self.WEST]:
            self._size = DispSize(320, 240)
        else:
            self._size = DispSize(240, 320)

        if hasattr(self, "spi_handle"):
            madctl = madctl_values[rotation]
            self._mv = (madctl >> 5) & 0x01
            if self._bgr:
                madctl |= 0x08
            self._write_command(self._CMD["MADCTL"])
            self._write_data(madctl)

    def set_window(self, x0: int, y0: int, x1: int, y1: int):
        """描画ウィンドウを設定する"""
        if self._mv:
            tx0, tx1 = x0 + self._y_offset, x1 + self._y_offset
            ty0, ty1 = y0 + self._x_offset, y1 + self._x_offset
        else:
            tx0, tx1 = x0 + self._x_offset, x1 + self._x_offset
            ty0, ty1 = y0 + self._y_offset, y1 + self._y_offset

        self._write_command(self._CMD["CASET"])
        self._write_data([tx0 >> 8, tx0 & 0xFF, tx1 >> 8, tx1 & 0xFF])
        self._write_command(self._CMD["RASET"])
        self._write_data([ty0 >> 8, ty0 & 0xFF, ty1 >> 8, ty1 & 0xFF])
        self._write_command(self._CMD["RAMWR"])

    def write_pixels(self, pixel_bytes: bytes):
        """ピクセルデータを書き込む"""
        data_len = len(pixel_bytes)

        self._set_dc_level(1)
        self._set_cs_level(0)

        if data_len <= self.CHUNK_SIZE:
            self.pi.spi_write(self.spi_handle, pixel_bytes)
        else:
            for i in range(0, data_len, self.CHUNK_SIZE):
                self.pi.spi_write(
                    self.spi_handle, pixel_bytes[i : i + self.CHUNK_SIZE]
                )
        self._set_cs_level(1)

    def display(self, image: Image.Image, full: bool = False):
        """
        全画面イメージを表示。
        前回の表示イメージと比較し、差分のある矩形領域（Dirty Rectangle）のみを更新することで、
        通信データ量とCPU負荷を最小限に抑える。
        """
        if image.size != self._size:
            image = image.resize(self._size)

        # 初回表示、または強制更新指定がある場合は全画面表示
        if full or self._last_image is None:
            img_array = np.array(image)
            pixel_bytes = self._color_converter.convert(img_array)
            self.set_window(0, 0, self.size.width - 1, self.size.height - 1)
            self.write_pixels(pixel_bytes)
            self._last_image = image.copy()
            return

        # 前回のイメージとの差分領域 (Bounding Box) を高速に取得
        diff_bbox = ImageChops.difference(image, self._last_image).getbbox()

        if diff_bbox is None:
            return

        # diff_bbox は (left, upper, right, lower)
        region_img = image.crop(diff_bbox)
        region_arr = np.array(region_img)
        pixel_bytes = self._color_converter.convert(region_arr)

        self.set_window(
            diff_bbox[0], diff_bbox[1], diff_bbox[2] - 1, diff_bbox[3] - 1
        )
        self.write_pixels(pixel_bytes)

        self._last_image = image.copy()

    def display_region(
        self, image: Image.Image, x0: int, y0: int, x1: int, y1: int
    ):
        """部分更新"""
        region = clamp_region(
            (x0, y0, x1, y1), self.size.width, self.size.height
        )
        if region[2] <= region[0] or region[3] <= region[1]:
            return
        region_img = image.crop(region)
        img_array = np.array(region_img)
        pixel_bytes = self._color_converter.convert(img_array)
        self.set_window(region[0], region[1], region[2] - 1, region[3] - 1)
        self.write_pixels(pixel_bytes)

        # _last_image の対応する領域を更新
        if self._last_image is None:
            self._last_image = Image.new("RGB", self._size, (0, 0, 0))

        self._last_image.paste(region_img, region)

    def close(self):
        """スリープさせて終了"""
        if hasattr(self, "spi_handle") and self.pi.connected:
            self._write_command(self._CMD["INVOFF"])
            self._write_command(self._CMD["DISPOFF"])
            self._write_command(self._CMD["SLPIN"])
            time.sleep(0.01)
        super().close()
