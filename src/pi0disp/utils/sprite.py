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
        Calculates the area that needs to be redrawn in (x, y, w, h) format.
        Includes a small margin to account for anti-aliasing and sub-pixel shifts.
        """
        if not self._dirty and self.prev_bbox is not None:
            return None
        res = merge_bboxes(self.prev_bbox, self.bbox)
        if res is None:
            return None

        # Add 2-pixel margin for anti-aliasing safety
        x0, y0, x1, y1 = res[0] - 2, res[1] - 2, res[2] + 2, res[3] + 2
        return (x0, y0, x1 - x0, y1 - y0)

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


class CircleSprite(Sprite):
    """
    A sprite representing a circular object.
    Can be manipulated using center coordinates (cx, cy) and radius.
    """

    __slots__ = ("_radius",)

    def __init__(self, cx: float, cy: float, radius: int):
        self._radius = radius
        super().__init__(
            x=cx - radius, y=cy - radius, width=radius * 2, height=radius * 2
        )

    @property
    def cx(self) -> float:
        """Returns the x-coordinate of the center."""
        return self._x + self._radius

    @cx.setter
    def cx(self, val: float):
        """Sets the x-coordinate of the center."""
        self.x = val - self._radius

    @property
    def cy(self) -> float:
        """Returns the y-coordinate of the center."""
        return self._y + self._radius

    @cy.setter
    def cy(self, val: float):
        """Sets the y-coordinate of the center."""
        self.y = val - self._radius

    @property
    def radius(self) -> int:
        """Returns the radius of the circle."""
        return self._radius

    @radius.setter
    def radius(self, val: int):
        """Sets the radius and updates size and position to keep the center."""
        if self._radius != val:
            # Maintain center
            cx, cy = self.cx, self.cy
            self._radius = val
            self.width = val * 2
            self.height = val * 2
            self.cx, self.cy = cx, cy
            self._dirty = True
