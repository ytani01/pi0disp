#
# (c) 2025 Yoichi Tanibayashi
#
import time
from typing import Union

import pigpio

from ..utils.mylogger import get_logger
from .disp_base import DispBase


class DispSpi(DispBase):
    """SPI Display."""

    DEF_PIN = {
        "rst": 25,
        "dc": 24,
        "bl": 23,
    }
    SPEED_HZ = {
        "default": 8_000_000,
        "max": 32_000_000,
    }

    def __init__(
        self,
        bl_at_close: bool = False,
        channel: int = 0,
        pin: dict = {
            "rst": DEF_PIN["rst"],
            "dc": DEF_PIN["dc"],
            "bl": DEF_PIN["bl"],
        },
        # rst_pin: int = DEF_PIN["rst"],
        # dc_pin: int = DEF_PIN["dc"],
        # backlight_pin: int = DEF_PIN["bl"],
        speed_hz: int = SPEED_HZ["default"],
        size: dict = {
            "width": DispBase.DEF_DISP["width"],
            "height": DispBase.DEF_DISP["height"],
        },
        # width: int = DispBase.DEF_DISP["width"],
        # height: int = DispBase.DEF_DISP["height"],
        rotation: int = DispBase.DEF_DISP["rotation"],
        debug=False,
    ):
        """Constractor.

        Args:
            bl_at_close (bool): backlight switch at close
            channel (int): SPI channel (0 or 1).
            pin (dict): {"rst": int, "dc": int, "bl": int}
            backlight_pin (int): GPIO pin for the backlight.
            speed_hz (int): SPI clock speed in Hz.
            size (dict): {"width": int, "height": int}
            rotation (int): Initial rotation (0, 90, 180, or 270 degrees).
            debug (bool): debug flag
        """
        super().__init__(size, rotation, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("bl_at_close=%s", bl_at_close)
        self.__log.debug("SPI: channel=%s,speed_hz=%s", channel, speed_hz)
        self.__log.debug("GPIO: pin=%s", pin)

        self.bl_at_close = bl_at_close

        self.pin = pin

        # Configure GPIO pins
        for p in self.pin:
            self.pi.set_mode(pin[p], pigpio.OUTPUT)

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

    def _write_command(self, command: int):
        """Sends a command byte to the display."""
        self.pi.write(self.pin["dc"], 0)  # D/C pin low for command
        self.pi.spi_write(self.spi_handle, [command])

    def _write_data(self, data: Union[int, bytes, list]):
        """Sends a data byte or buffer to the display."""
        self.pi.write(self.pin["dc"], 1)  # D/C pin high for data
        if isinstance(data, int):
            self.pi.spi_write(self.spi_handle, [data])
        else:
            self.pi.spi_write(self.spi_handle, data)

    def init_display(self):
        """Initialize Display."""
        self.__log.debug("backlight ON")

        # Hardware reset
        self.pi.write(self.pin["rst"], 1)
        time.sleep(0.01)
        self.pi.write(self.pin["rst"], 0)
        time.sleep(0.01)
        self.pi.write(self.pin["rst"], 1)
        time.sleep(0.150)

        self.pi.write(self.pin["bl"], 1)

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
            self.pi.write(self.pin["bl"], 1 if bl_sw else 0)

        super().close()  # pigpio
