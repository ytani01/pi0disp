#
# (c) 2025 Yoichi Tanibayashi
#
import time

import pigpio

from ..utils.mylogger import get_logger
from .disp_base import DispBase


class DispSpi(DispBase):
    """SPI Display."""

    DEF_PIN = {
        "RST": 25,
        "DC": 24,
        "BL": 23,
    }
    SPEED_HZ = {
        "default": 8_000_000,
        "max": 32_000_000,
    }

    def __init__(
        self,
        bl_at_close: bool = False,
        channel: int = 0,
        rst_pin: int = DEF_PIN["RST"],
        dc_pin: int = DEF_PIN["DC"],
        backlight_pin: int = DEF_PIN["BL"],
        speed_hz: int = SPEED_HZ["default"],
        width: int = DispBase.DEF_DISP["width"],
        height: int = DispBase.DEF_DISP["height"],
        rotation: int = DispBase.DEF_DISP["rotation"],
        debug=False,
    ):
        """Constractor.

        Args:
            bl_at_close (bool): backlight switch at close
            channel (int): SPI channel (0 or 1).
            rst_pin (int): GPIO pin for Reset.
            dc_pin (int): GPIO pin for Data/Command select.
            backlight_pin (int): GPIO pin for the backlight.
            speed_hz (int): SPI clock speed in Hz.
            width (int): The native width of the display.
            height (int): The native height of the display.
            rotation (int): Initial rotation (0, 90, 180, or 270 degrees).
            debug (bool): debug flag
        """
        super().__init__(width, height, rotation, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("bl_at_close=%s", bl_at_close)
        self.__log.debug("SPI: channel=%s,speed_hz=%s", channel, speed_hz)
        self.__log.debug(
            "GPIO: rst_pin=%s,dc_pin=%s,backlight_pin=%s",
            rst_pin,
            dc_pin,
            backlight_pin,
        )

        self.bl_at_close = bl_at_close

        self.rst_pin = rst_pin
        self.dc_pin = dc_pin
        self.backlight_pin = backlight_pin

        # Configure GPIO pins
        for pin in [self.rst_pin, self.dc_pin, self.backlight_pin]:
            self.pi.set_mode(pin, pigpio.OUTPUT)

        # Open SPI handle
        self.spi_handle = self.pi.spi_open(channel, speed_hz, 0)
        if self.spi_handle < 0:
            raise RuntimeError(
                f"Failed to open SPI bus: handle={self.spi_handle}"
            )

    def __enter__(self):
        self.__log.debug("")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__log.debug(
            "exc_type=%s,exc_val=%s,exc_tb=%s", exc_type, exc_val, exc_tb
        )
        self.close()

    def init_display(self):
        """Initialize Display."""
        self.__log.debug("backlight ON")

        # Hardware reset
        self.pi.write(self.rst_pin, 1)
        time.sleep(0.01)
        self.pi.write(self.rst_pin, 0)
        time.sleep(0.01)
        self.pi.write(self.rst_pin, 1)
        time.sleep(0.150)

        self.pi.write(self.backlight_pin, 1)

    def close(self, bl: bool | None = None):
        """Cleans up resources.

        Args:
            bl (bool | None): バックライトの状態
                              省略すると、生成時のオプションを使う
        """
        if self.pi.connected:
            # backlight
            bl_sw = self.bl_at_close
            if bl:
                bl_sw = bl
            self.pi.write(self.backlight_pin, 1 if bl_sw else 0)

        super().close()  # pigpio
