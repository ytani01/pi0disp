#
# (c) 2025 Yoichi Tanibayashi
#
from importlib.metadata import version

if __package__:
    __version__ = version(__package__)
else:
    __version__ = "_._._"

from .my_logger import get_logger
from .st7789v import ST7789V

__all__ = [
    "__version__",
    "ST7789V",
    "get_logger",
]
