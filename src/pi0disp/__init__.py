#
# (c) 2025 Yoichi Tanibayashi
#
from importlib.metadata import version

if __package__:
    __version__ = version(__package__)
else:
    __version__ = "_._._"

from .utils.my_logger import get_logger
from .disp.st7789v import ST7789V
from .utils.utils import ImageProcessor, get_ip_address, draw_text

__all__ = [
    "__version__",
    "ST7789V",
    "get_logger",
    "ImageProcessor",
    "get_ip_address",
    "draw_text",
]
