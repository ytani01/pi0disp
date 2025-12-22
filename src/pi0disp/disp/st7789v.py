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
    An optimized driver for ST7789V-based SPI displays.
    """

    CMD = {
        "SWRESET": 0x01,
        "SLPIN": 0x10,
        "SLPOUT": 0x11,
        "NORON": 0x13,
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
        debug=False,
    ):
        """
        Initializes the display driver.
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

        # Initialize the optimizer pack
        self._optimizers = create_optimizer_pack()
        self._last_window: Optional[Tuple[int, int, int, int]] = None

        self.init_display()
        self.set_rotation(self._rotation)

    def init_display(self):
        """Performs the hardware initialization sequence for the ST7789V."""
        super().init_display()
        self.__log.debug("")

        # Initialization sequence
        self._write_command(self.CMD["SWRESET"])
        time.sleep(0.150)
        self._write_command(self.CMD["SLPOUT"])
        time.sleep(0.5)
        self._write_command(self.CMD["COLMOD"])
        self._write_data(0x55)  # 16 bits per pixel
        self._write_command(self.CMD["INVON"])
        self._write_command(self.CMD["NORON"])
        self._write_command(self.CMD["DISPON"])
        time.sleep(0.1)

    def set_rotation(self, rotation: int):
        """Sets the display rotation."""
        self.rotation = rotation
        self.__log.debug("%s", self.__class__.__name__)

        madctl_values = {0: 0x00, 90: 0x60, 180: 0xC0, 270: 0xA0}
        if rotation not in madctl_values:
            raise ValueError("Rotation must be 0, 90, 180, or 270.")

        if hasattr(self, "spi_handle"):
            self._write_command(self.CMD["MADCTL"])
            self._write_data(madctl_values[rotation])

        self._last_window = None  # Invalidate window cache

    def set_window(self, x0: int, y0: int, x1: int, y1: int):
        """Sets the active drawing window on the display."""
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
        """Writes a raw buffer of pixel data to the current window."""
        chunk_size = self._optimizers["adaptive_chunking"].get_chunk_size()
        data_len = len(pixel_bytes)

        self.pi.write(self.pin.dc, 1)  # Set D/C high for data

        if data_len <= chunk_size:
            self.pi.spi_write(self.spi_handle, pixel_bytes)
        else:
            for i in range(0, data_len, chunk_size):
                self.pi.spi_write(
                    self.spi_handle, pixel_bytes[i : i + chunk_size]
                )

    def display(self, image: Image.Image):
        """Displays a full PIL Image on the screen."""
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
        """Displays a portion of a PIL image within the specified region."""
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

    # def close(self, bl: bool | None = None):
    #     """Cleans up resources."""
    #     super().close(bl)

    def dispoff(self):
        """DISPOFF."""
        self._write_command(self.CMD["DISPOFF"])
        self.set_backlight(False)

    def sleep(self):
        """Puts the display into sleep mode."""
        self._write_command(self.CMD["SLPIN"])
        self.set_backlight(False)

    def wake(self):
        """Wakes the display from sleep mode."""
        self._write_command(self.CMD["SLPOUT"])
        self.set_backlight(True)
