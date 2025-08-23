#
# (c) 2025 Yoichi Tanibayashi
#
"""
pi0disp/utils/sprite.py

Provides a base class for creating animated objects (sprites).
"""
from typing import Tuple, Optional
from abc import ABC, abstractmethod
from PIL import ImageDraw

from pi0disp.utils.utils import merge_bboxes, expand_bbox


class Sprite(ABC):
    """
    A base class for animated objects (sprites).
    Manages position, size, and dirty regions for efficient redrawing.
    """
    def __init__(self, x: float, y: float, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.prev_bbox: Optional[Tuple[int, int, int, int]] = None

    @property
    def bbox(self) -> Tuple[int, int, int, int]:
        """Returns the sprite's current bounding box as integer coordinates."""
        return (int(self.x), int(self.y), int(self.x + self.width), int(self.y + self.height))

    def get_dirty_region(self) -> Optional[Tuple[int, int, int, int]]:
        """
        Calculates the area that needs to be redrawn for the current frame
        by merging the previous and current bounding boxes.
        """
        return merge_bboxes(self.prev_bbox, self.bbox)

    def record_current_bbox(self):
        """
        Records the current bounding box. This should be called after drawing
        to prepare for the next frame's dirty region calculation.
        """
        self.prev_bbox = self.bbox

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
