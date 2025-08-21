# -*- coding: utf-8 -*-
"""
pi0disp project utility functions.

This module provides high-level utility functions and classes that leverage
the `performance_core` module for optimized operations, such as color
conversion, region management, and image processing.
"""
from typing import List, Tuple, Optional

import numpy as np
from PIL import Image

from .performance_core import create_optimizer_pack

# --- Module-level Singleton ---
# A single, shared instance of the optimizer pack for all utility functions.
# This avoids repeated object creation and shares caches (e.g., LUTs).
_OPTIMIZER_PACK = None

def _get_optimizers():
    """Lazy initializer for the singleton optimizer pack."""
    global _OPTIMIZER_PACK
    if _OPTIMIZER_PACK is None:
        _OPTIMIZER_PACK = create_optimizer_pack()
    return _OPTIMIZER_PACK

# --- Core Utility Functions ---

def pil_to_rgb565_bytes(img: Image.Image) -> bytes:
    """
    Converts a PIL Image to a big-endian RGB565 byte string using an
    optimized color converter.

    Args:
        img: The PIL Image to convert.

    Returns:
        A byte string of the image data in RGB565 format.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    np_img = np.array(img, dtype=np.uint8)
    return _get_optimizers()['color_converter'].rgb_to_rgb565_bytes(np_img)


def merge_bboxes(bbox1: Optional[Tuple[int, int, int, int]], 
                bbox2: Optional[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    """
    Merges two bounding boxes into a single bounding box that encloses both.

    Args:
        bbox1: The first bounding box (x0, y0, x1, y1) or None.
        bbox2: The second bounding box (x0, y0, x1, y1) or None.

    Returns:
        The merged bounding box, or the non-None box if one is None.
    """
    if bbox1 is None:
        return bbox2
    if bbox2 is None:
        return bbox1
    
    return _get_optimizers()['region_optimizer']._merge_two(bbox1, bbox2)


def optimize_dirty_regions(regions: List[Tuple[int, int, int, int]], 
                          max_regions: int = 8) -> List[Tuple[int, int, int, int]]:
    """
    Optimizes a list of "dirty" regions by merging overlapping or
    nearby regions to reduce the total number of update areas.

    Args:
        regions: A list of bounding boxes to optimize.
        max_regions: The maximum number of regions to return.

    Returns:
        An optimized list of merged regions.
    """
    return _get_optimizers()['region_optimizer'].merge_regions(regions, max_regions)


def clamp_region(region: Tuple[int, int, int, int], 
                width: int, height: int) -> Tuple[int, int, int, int]:
    """
    Clamps a region's coordinates to ensure it is within the screen boundaries.

    Args:
        region: The region (x0, y0, x1, y1) to clamp.
        width: The maximum width (exclusive).
        height: The maximum height (exclusive).

    Returns:
        The clamped region.
    """
    return _get_optimizers()['region_optimizer'].clamp_region(region, width, height)

# --- High-Level Image Processor ---

class ImageProcessor:
    """
    A utility class for performing common, high-level image processing tasks.
    """
    def __init__(self):
        # This class can have its own optimizer pack if needed, but for now
        # it uses the shared one for simplicity.
        self.optimizers = _get_optimizers()

    def resize_with_aspect_ratio(self, 
                                img: Image.Image, 
                                target_width: int, 
                                target_height: int,
                                fit_mode: str = "contain") -> Image.Image:
        """
        Resizes an image while maintaining its aspect ratio.

        Args:
            img: The source PIL Image.
            target_width: The width of the target canvas.
            target_height: The height of the target canvas.
            fit_mode: "contain" (fits image inside, letterboxing if needed)
                      "cover" (covers the canvas, cropping if needed).

        Returns:
            A new PIL Image resized and fitted to the target dimensions.
        """
        img_ratio = img.width / img.height
        target_ratio = target_width / target_height
        
        if fit_mode == "contain":
            if img_ratio > target_ratio:
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                new_height = target_height
                new_width = int(target_height * img_ratio)
        elif fit_mode == "cover":
            if img_ratio < target_ratio:
                new_width = target_width
                new_height = int(target_width / img_ratio)
            else:
                new_height = target_height
                new_width = int(target_height * img_ratio)
        else:
            raise ValueError(f"Unknown fit_mode: {fit_mode}")

        resized = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        if fit_mode == "contain":
            # Create a black canvas and paste the resized image in the center
            result = Image.new("RGB", (target_width, target_height), (0, 0, 0))
            paste_x = (target_width - new_width) // 2
            paste_y = (target_height - new_height) // 2
            result.paste(resized, (paste_x, paste_y))
            return result
        
        # For "cover", crop the center of the resized image
        crop_x = (new_width - target_width) // 2
        crop_y = (new_height - target_height) // 2
        return resized.crop((crop_x, crop_y, crop_x + target_width, crop_y + target_height))
    
    def apply_gamma(self, img: Image.Image, gamma: float = 2.2) -> Image.Image:
        """
        Applies gamma correction to an image.

        Args:
            img: The source PIL Image.
            gamma: The gamma value to apply.

        Returns:
            A new gamma-corrected PIL Image.
        """
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        np_img = np.array(img, dtype=np.uint8)
        corrected = self.optimizers['color_converter'].apply_gamma(np_img, gamma)
        
        return Image.fromarray(corrected, "RGB")