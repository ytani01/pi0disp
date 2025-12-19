#
# (c) 2025 Yoichi Tanibayashi
#
import time
from typing import NamedTuple, Optional, Union

import pigpio

from ..utils.mylogger import errmsg, get_logger
from .disp_base import DispBase, DispSize


class SpiPins(NamedTuple):
    """SPI Pins class."""

    rst: int
    dc: int
    bl: Optional[int] = None
    cs: Optional[int] = None


class DispSpi(DispBase):
    """SPI Display."""

    DEF_PIN = SpiPins(rst=25, dc=24, bl=23)
    SPEED_HZ = {
        "default": 8_000_000,
        "max": 32_000_000,
    }

    def __init__(
        self,
        bl_at_close: bool = False,
        channel: int = 0,
        pin: SpiPins | None = None,
        speed_hz: int = SPEED_HZ["default"],
        size: DispSize | None = None,
        rotation: int = DispBase.DEF_ROTATION,
        brightness: int = 255,
        debug=False,
    ):
        super().__init__(size, rotation, debug=debug)
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("bl_at_close=%s", bl_at_close)
        self.__log.debug("SPI: channel=%s,speed_hz=%s", channel, speed_hz)
        self.__log.debug("GPIO: pin=%s", pin)

        self.bl_at_close = bl_at_close

        if pin is None:
            pin = self.DEF_PIN

        self.pin = pin
        self._brightness = brightness
        self._backlight_on = False

        # Configure GPIO pins
        for p_val in [self.pin.rst, self.pin.dc, self.pin.bl, self.pin.cs]:
            if p_val is not None:
                self.pi.set_mode(p_val, pigpio.OUTPUT)

        # Open SPI handle
        # SPI handle options: if CS is controlled by pigpio, channel is usually used.
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
        self.pi.write(self.pin.dc, 0)  # D/C pin low for command
        self.pi.spi_write(self.spi_handle, [command])

    def _write_data(self, data: Union[int, bytes, list]):
        """Sends a data byte or buffer to the display."""
        self.pi.write(self.pin.dc, 1)  # D/C pin high for data
        if isinstance(data, int):
            self.pi.spi_write(self.spi_handle, [data])
        else:
            self.pi.spi_write(self.spi_handle, data)

    def set_brightness(self, brightness: int):
        """Sets the backlight brightness (0-255)."""
        if not self.pin.bl:
            self.__log.debug("pin.bl=%s: do nothing", self.pin.bl)
            return

        # self.set_backlightのON/OFFに関わらず、値を保持する。
        self._brightness = max(0, min(255, brightness))

        if self._backlight_on:
            self.pi.set_PWM_dutycycle(self.pin.bl, self._brightness)

    def set_backlight(self, on: bool):
        """Turns the backlight on or off.

        self._brightness の値は維持される
        """
        if not self.pin.bl:
            self.__log.debug("pin.bl=%s: do nothing", self.pin.bl)
            return

        self._backlight_on = on

        if on:
            self.pi.set_PWM_dutycycle(self.pin.bl, self._brightness)
        else:
            self.pi.set_PWM_dutycycle(self.pin.bl, 0)

    def init_display(self):
        """Initialize Display."""
        self.__log.debug("backlight ON")

        # Hardware reset
        self.pi.write(self.pin.rst, 1)
        time.sleep(0.01)
        self.pi.write(self.pin.rst, 0)
        time.sleep(0.01)
        self.pi.write(self.pin.rst, 1)
        time.sleep(0.150)

        self.set_backlight(True)

    def close(self, bl: bool | None = None):
        """Cleans up resources.

        Args:
            bl (bool | None): バックライトの状態
                              省略すると、生成時のオプションを使う
        """
        if self.pi.connected:
            # SPI handle
            if self.spi_handle >= 0:
                try:
                    self.pi.spi_close(self.spi_handle)
                    self.__log.debug(
                        "spi_handl=%s: close SPI", self.spi_handle
                    )
                except Exception as e:
                    self.__log.warning(errmsg(e))

            # backlight
            if self.pin.bl is not None:
                bl_sw = False
                if bl:
                    bl_sw = bl
                else:
                    bl_sw = self.bl_at_close
                self.set_backlight(bl_sw)
        else:
            self.__log.warning("pi.connected=%s", self.pi.connected)

        super().close()  # self.pi の終了処理(stop)は、親クラスに任せる
