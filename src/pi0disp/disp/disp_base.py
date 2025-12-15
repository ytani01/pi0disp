#
# (c) 2025 Yoichi Tanibayashi
#
import pigpio
from PIL import Image

from ..utils.mylogger import get_logger


class DispBase:
    """Base class of display."""

    DEF_DISP = {
        "width": 240,
        "height": 320,
        "rotation": 270,
    }

    def __init__(self, size: dict, rotation, debug=False):
        """Constractor."""
        self.__debug = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)
        self.__log.debug("disp_size=%s,rotation=%s", size, rotation)

        self._native_size = size
        self.size = size
        self._rotation = rotation

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
            self.size["width"], self.size["height"] = (
                self._native_size["height"],
                self._native_size["width"],
            )
        else:
            self.size["width"], self.size["height"] = (
                self._native_size["width"],
                self._native_size["height"],
            )

        self._rotation = rotation

    def display(self, image: Image.Image):
        """display."""
        self.__log.debug("adjust image size")
        if image.size != (self.size["width"], self.size["height"]):
            image = image.resize((self.size["width"], self.size["height"]))

    def close(self):
        """Close."""
        if self.pi.connected:
            self.pi.stop()
