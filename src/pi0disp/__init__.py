#
# (c) 2025 Yoichi Tanibayashi
#
from importlib.metadata import PackageNotFoundError, version

from .disp.disp_base import DispBase, DispSize
from .disp.disp_spi import DispSpi, SpiPins
from .disp.st7789v import ST7789V
from .utils.click_utils import click_common_opts
from .utils.my_conf import MyConf
from .utils.mylogger import errmsg, get_logger
from .utils.performance_core import RegionOptimizer
from .utils.sprite import Sprite
from .utils.utils import (
    ImageProcessor,
    draw_text,
    expand_bbox,
    get_ip_address,
)

if __package__:
    try:
        __version__ = version(__package__)
    except PackageNotFoundError:
        __version__ = "0.0.0"
else:
    __version__ = "_._._"

__all__ = [
    "__version__",
    "errmsg",
    "get_logger",
    "click_common_opts",
    "draw_text",
    "get_ip_address",
    "expand_bbox",
    "DispBase",
    "DispSize",
    "DispSpi",
    "MyConf",
    "RegionOptimizer",
    "SpiPins",
    "Sprite",
    "ST7789V",
    "ImageProcessor",
    "get_ip_address",
    "draw_text",
]
