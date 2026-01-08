#
# (c) 2025 Yoichi Tanibayashi
#
"""
pi0disp/utils/sprite.py

Provides a base class for creating animated objects (sprites).
"""

from abc import ABC, abstractmethod
from typing import Optional, Tuple

from PIL import ImageDraw

from pi0disp.utils.utils import merge_bboxes


class Sprite(ABC):
    """
    A base class for animated objects (sprites).
    Manages position, size, and dirty regions for efficient redrawing.
    """

    __slots__ = ("_x", "_y", "_width", "_height", "prev_bbox", "_dirty")

    def __init__(self, x: float, y: float, width: int, height: int):
        self._x = x
        self._y = y
        self._width = width
        self._height = height
        self.prev_bbox: Optional[Tuple[int, int, int, int]] = None
        self._dirty = True

    @property
    def x(self) -> float:
        """Returns the x-coordinate of the top-left corner."""
        return self._x

    @x.setter
    def x(self, val: float):
        """Sets the x-coordinate and marks the sprite as dirty if changed."""
        if self._x != val:
            self._x = val
            self._dirty = True

    @property
    def y(self) -> float:
        """Returns the y-coordinate of the top-left corner."""
        return self._y

    @y.setter
    def y(self, val: float):
        """Sets the y-coordinate and marks the sprite as dirty if changed."""
        if self._y != val:
            self._y = val
            self._dirty = True

    @property
    def width(self) -> int:
        """Returns the width of the sprite."""
        return self._width

    @width.setter
    def width(self, val: int):
        """Sets the width and marks the sprite as dirty if changed."""
        if self._width != val:
            self._width = val
            self._dirty = True

    @property
    def height(self) -> int:
        """Returns the height of the sprite."""
        return self._height

    @height.setter
    def height(self, val: int):
        """Sets the height and marks the sprite as dirty if changed."""
        if self._height != val:
            self._height = val
            self._dirty = True

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Returns the sprite's current bounding box as integer coordinates."""
        return (
            int(self._x),
            int(self._y),
            int(self._x + self._width),
            int(self._y + self._height),
        )

    def get_dirty_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Calculates the area that needs to be redrawn for the current frame.
        If the sprite state hasn't changed since the last record_current_bbox call,
        it returns None to skip redundant display updates.
        """
        if not self._dirty and self.prev_bbox is not None:
            return None
        return merge_bboxes(self.prev_bbox, self.bbox)

    def record_current_bbox(self):
        """
        Records the current bounding box and resets the dirty flag.
        This should be called after drawing to prepare for the next frame's
        dirty region calculation.
        """
        self.prev_bbox = self.bbox
        self._dirty = False

    @abstractmethod
    def update(self, delta_t: float):
        """
        Updates the sprite's state (e.g., position, animation frame).

        Args:
            delta_t (float): Time elapsed since the last frame in seconds.
        """
        pass

    @abstractmethod
    def draw(self, draw: ImageDraw.ImageDraw):
        """
        Draws the sprite onto the provided PIL ImageDraw object.

        Args:
            draw (ImageDraw.ImageDraw): The drawing context to use.
        """
        pass
