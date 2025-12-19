#
# (c) 2025 Yoichi Tanibayashi
#
import time
from typing import Union

import pigpio

from ..utils.mylogger import get_logger
from .disp_base import DispBase, Size


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
        pin: dict | None = None,
        speed_hz: int = SPEED_HZ["default"],
        size: Size | None = None,
        rotation: int = DispBase.DEF_ROTATION,
        debug=False,
    ):
        if pin is None:
            pin = self.DEF_PIN
        if size is None:
            size = DispBase.DEF_SIZE

        super().__init__(size, rotation, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("bl_at_close=%s", bl_at_close)
        self.__log.debug("SPI: channel=%s,speed_hz=%s", channel, speed_hz)
        self.__log.debug("GPIO: pin=%s", pin)

        self.bl_at_close = bl_at_close

        self.pin = pin

        # Configure GPIO pins
        for p_val in self.pin.values():
            self.pi.set_mode(p_val, pigpio.OUTPUT)

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
