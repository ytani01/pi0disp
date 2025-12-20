#
# (c) 2025 Yoichi Tanibayashi
#
from abc import ABCMeta
from typing import NamedTuple

import pigpio
from PIL import Image

from ..utils.my_conf import MyConf
from ..utils.mylogger import get_logger


class DispSize(NamedTuple):
    """Display size class."""

    width: int
    height: int


class DispBase(metaclass=ABCMeta):
    """Display Base."""

    DEF_SIZE = DispSize(240, 320)
    DEF_ROTATION = 0

    def __init__(
        self,
        size: DispSize | None = None,
        rotation: int | None = None,
        debug=False,
    ):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("size=%s,rotation=%s", size, rotation)

        # load configuration file
        self._conf = MyConf(debug=self.__debug)

        # size
        if size is None:
            if self._conf.data.get("width") and self._conf.data.get("height"):
                size = DispSize(self._conf.data.width, self._conf.data.height)
                self.__log.debug("size=%s [conf]", size)
            else:
                size = self.DEF_SIZE
                self.__log.debug("size=%s [DEF_SIZE]", size)
        self._native_size = size
        self._size = size

        # rotation
        if rotation is None:
            if self._conf.data.get("rotation"):
                rotation = self._conf.data.rotation
                self.__log.debug("rotation=%s [conf]", rotation)
            else:
                rotation = self.DEF_ROTATION
                self.__log.debug("rotation=%s [DEF_ROTATION]", rotation)
        self._rotation = rotation

        # Initialize pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio daemon. Is it running?"
            )

    def __enter__(self):
        self.__log.debug("")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.__log.debug(
            "exc_type=%s,exc_val=%s,exc_tb=%s", exc_type, exc_val, exc_tb
        )
        self.close()

    @property
    def size(self):
        """Property: size"""
        return self._size

    @property
    def native_size(self):
        """Property: native size"""
        return self._native_size

    @property
    def rotation(self):
        """Property: rotation"""
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: int):
        """Sets the display rotation."""
        # self.__log.debug("rotation=%s", rotation)

        # Swap width and height for portrait/landscape modes
        if rotation in (90, 270):
            self._size = DispSize(
                self._native_size.height, self._native_size.width
            )
        else:
            self._size = self._native_size

        self._rotation = rotation

    @property
    def conf(self):
        """Conf."""
        return self._conf

    def init_display(self):
        """Initialize display."""
        self.__log.warning("Please override this method.")

    def display(self, image: Image.Image):
        """display."""
        self.__log.debug("adjust image size")
        if image.size != self._size:
            image = image.resize(self._size)

    def close(self):
        """Close."""
        if self.pi.connected:
            self.__log.debug("close pigpiod connection")
            self.pi.stop()
        else:
            self.__log.warning("self.pi.conencted=%s", self.pi.connected)
