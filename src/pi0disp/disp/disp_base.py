#
# (c) 2025 Yoichi Tanibayashi
#
from abc import ABCMeta
from typing import NamedTuple

import pigpio
from PIL import Image

from ..utils.mylogger import get_logger


class DispSize(NamedTuple):
    """Display size class."""

    width: int
    height: int


class DispBase(metaclass=ABCMeta):
    """Display Base."""

    DEF_SIZE = DispSize(240, 320)
    DEF_ROTATION = 270

    def __init__(self, size: DispSize, rotation: int, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("disp_size=%s,rotation=%s", size, rotation)

        self._native_size = size
        self.size = size
        self.set_rotation(rotation)

        # Initialize pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio daemon. Is it running?"
            )

    def init_display(self):
        """Initialize display."""
        self.__log.warning("Please override this method.")

    def set_rotation(self, rotation: int):
        """Sets the display rotation."""
        self.__log.debug("rotation=%s", rotation)

        # Swap width and height for portrait/landscape modes
        if rotation in (90, 270):
            self.size = DispSize(
                self._native_size.height, self._native_size.width
            )
        else:
            self.size = self._native_size

        self._rotation = rotation

    def display(self, image: Image.Image):
        """display."""
        self.__log.debug("adjust image size")
        if image.size != self.size:
            image = image.resize(self.size)

    def close(self):
        """Close."""
        if self.pi.connected:
            self.pi.stop()
