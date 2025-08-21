# -*- coding: utf-8 -*-
"""
pi0disp project utility functions.

This module provides high-level utility functions and classes that leverage
the `performance_core` module for optimized operations, such as color
conversion, region management, and image processing.
"""
import socket
from typing import List, Tuple, Optional, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .my_logger import get_logger
from .performance_core import create_optimizer_pack

log = get_logger(__name__)

# --- Module-level Singleton ---
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
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    np_img = np.array(img, dtype=np.uint8)
    return _get_optimizers()['color_converter'].rgb_to_rgb565_bytes(np_img)

def merge_bboxes(bbox1: Optional[Tuple[int, int, int, int]], 
                bbox2: Optional[Tuple[int, int, int, int]]) -> Optional[Tuple[int, int, int, int]]:
    """
    Merges two bounding boxes into a single bounding box that encloses both.
    """
    if bbox1 is None: return bbox2
    if bbox2 is None: return bbox1
    return _get_optimizers()['region_optimizer']._merge_two(bbox1, bbox2)

def optimize_dirty_regions(regions: List[Tuple[int, int, int, int]], 
                          max_regions: int = 8) -> List[Tuple[int, int, int, int]]:
    """
    Optimizes a list of "dirty" regions by merging overlapping or
    nearby regions to reduce the total number of update areas.
    """
    return _get_optimizers()['region_optimizer'].merge_regions(regions, max_regions)

def clamp_region(region: Tuple[int, int, int, int], 
                width: int, height: int) -> Tuple[int, int, int, int]:
    """
    Clamps a region's coordinates to ensure it is within the screen boundaries.
    """
    return _get_optimizers()['region_optimizer'].clamp_region(region, width, height)

# --- High-Level Image Processor ---

class ImageProcessor:
    """
    A utility class for performing common, high-level image processing tasks.
    """
    def __init__(self):
        self.optimizers = _get_optimizers()

    def resize_with_aspect_ratio(self, 
                                img: Image.Image, 
                                target_width: int, 
                                target_height: int,
                                fit_mode: str = "contain") -> Image.Image:
        """
        Resizes an image while maintaining its aspect ratio.
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
        
        crop_x = (new_width - target_width) // 2
        crop_y = (new_height - target_height) // 2
        return resized.crop((crop_x, crop_y, crop_x + target_width, crop_y + target_height))
    
    def apply_gamma(self, img: Image.Image, gamma: float = 2.2) -> Image.Image:
        """
        Applies gamma correction to an image.
        """
        if img.mode != "RGB":
            img = img.convert("RGB")
        np_img = np.array(img, dtype=np.uint8)
        corrected = self.optimizers['color_converter'].apply_gamma(np_img, gamma)
        return Image.fromarray(corrected, "RGB")

# --- General Purpose Utilities ---

def get_ip_address() -> str:
    """
    Tries to determine the local IP address by connecting to an external server.
    Returns "IP not found" if unsuccessful.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2.0)
        s.connect(('8.8.8.8', 80))
        ip = s.getsockname()[0]
    except (socket.timeout, OSError) as e:
        log.warning(f"Could not get IP address: {e}")
        ip = "IP not found"
    finally:
        s.close()
    return ip

def draw_text(draw: ImageDraw.Draw, text: str, font: ImageFont.ImageFont, 
              x: Union[int, str], y: Union[int, str], 
              width: int, height: int, color: Tuple[int, int, int],
              padding: int = 5) -> Tuple[int, int, int, int]:
    """
    Draws text on a PIL ImageDraw object with flexible positioning.
    It pre-renders the text to accurately determine its bounding box.

    Args:
        draw: The ImageDraw object to draw on.
        text: The text string to display.
        font: The ImageFont object to use.
        x: The horizontal position. Can be an integer (coordinate) or a
           string ('left', 'center', 'right').
        y: The vertical position. Can be an integer (coordinate) or a
           string ('top', 'center', 'bottom').
        width: The width of the image canvas.
        height: The height of the image canvas.
        color: The text color as an RGB tuple.
        padding: The padding in pixels to use for keyword-based positions.

    Returns:
        The bounding box of the drawn text (x0, y0, x1, y1).
    """
    # Pre-render text to a temporary image to get accurate bounding box
    # Create a temporary image large enough to contain the text
    temp_img = Image.new('RGBA', (width, height), (0, 0, 0, 0))
    temp_draw = ImageDraw.Draw(temp_img)
    temp_draw.text((0, 0), text, font=font, fill=color)

    # Get the actual bounding box of the drawn pixels
    actual_bbox = temp_img.getbbox()

    if actual_bbox is None:
        # Text is empty or completely transparent, return a zero-sized bbox
        return (0, 0, 0, 0)

    text_width = actual_bbox[2] - actual_bbox[0]
    text_height = actual_bbox[3] - actual_bbox[1]

    # Calculate X coordinate
    if isinstance(x, str):
        if x == 'left':
            final_x = padding
        elif x == 'center':
            final_x = (width - text_width) // 2
        elif x == 'right':
            final_x = width - text_width - padding
        else:
            log.warning(f"Invalid keyword for x: '{x}'. Defaulting to 'left'.")
            final_x = padding
    else:
        final_x = x

    # Calculate Y coordinate
    if isinstance(y, str):
        if y == 'top':
            final_y = padding
        elif y == 'center':
            final_y = (height - text_height) // 2
        elif y == 'bottom':
            final_y = height - text_height - padding
        else:
            log.warning(f"Invalid keyword for y: '{y}'. Defaulting to 'top'.")
            final_y = padding
    else:
        final_y = y
        
    final_pos = (final_x, final_y)
    
    # Draw the text on the actual draw object
    draw.text(final_pos, text, font=font, fill=color)
    
    # Return the bounding box of the drawn text for dirty region tracking
    # Adjust for the actual_bbox offset if text was not drawn at (0,0) on temp_img
    return (
        final_pos[0] + actual_bbox[0],
        final_pos[1] + actual_bbox[1],
        final_pos[0] + actual_bbox[2],
        final_pos[1] + actual_bbox[3]
    )
