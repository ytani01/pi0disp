# -*- coding: utf-8 -*-
"""
pi0disp project utility functions.

This module provides high-level utility functions and classes for image
processing, region management, and display operations.
"""

import socket
from typing import Optional, Tuple, Union

import numpy as np
from PIL import Image, ImageDraw, ImageFont

from .mylogger import get_logger
from .performance_core import ColorConverter

log = get_logger(__name__)

# --- Module-level Singleton for performance ---
_COLOR_CONVERTER = ColorConverter()


# --- Core Utility Functions ---


def pil_to_rgb565_bytes(img: Image.Image, apply_gamma: bool = False) -> bytes:
    """
    Converts a PIL Image to a big-endian RGB565 byte string using an
    optimized color converter.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    np_img = np.array(img, dtype=np.uint8)
    return _COLOR_CONVERTER.convert(np_img, apply_gamma=apply_gamma)


def merge_bboxes(
    bbox1: Optional[Tuple[int, int, int, int]],
    bbox2: Optional[Tuple[int, int, int, int]],
) -> Optional[Tuple[int, int, int, int]]:
    """
    Merges two bounding boxes into a single bounding box that encloses both.
    """
    if bbox1 is None:
        return bbox2
    if bbox2 is None:
        return bbox1
    return (
        min(bbox1[0], bbox2[0]),
        min(bbox1[1], bbox2[1]),
        max(bbox1[2], bbox2[2]),
        max(bbox1[3], bbox2[3]),
    )


def clamp_region(
    region: Tuple[int, int, int, int], width: int, height: int
) -> Tuple[int, int, int, int]:
    """
    Clamps a region's coordinates to ensure it is within the screen boundaries.
    """
    return (
        max(0, region[0]),
        max(0, region[1]),
        min(width, region[2]),
        min(height, region[3]),
    )


def expand_bbox(
    bbox: Tuple[int, int, int, int], expansion: int
) -> Tuple[int, int, int, int]:
    """
    Expands a bounding box by a given number of pixels on all sides.
    """
    return (
        bbox[0] - expansion,
        bbox[1] - expansion,
        bbox[2] + expansion,
        bbox[3] + expansion,
    )


# --- High-Level Image Processor ---


class ImageProcessor:
    """
    A utility class for performing common,
    high-level image processing tasks.
    """

    def __init__(self, gamma: float = 2.2):
        self._converter = ColorConverter(gamma=gamma)

    def resize_with_aspect_ratio(
        self,
        img: Image.Image,
        target_width: int,
        target_height: int,
        fit_mode: str = "contain",
    ) -> Image.Image:
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

        resized = img.resize(
            (new_width, new_height), Image.Resampling.LANCZOS
        )

        if fit_mode == "contain":
            # Create a black canvas and paste the resized image in the center
            result = Image.new(
                "RGB", (target_width, target_height), (0, 0, 0)
            )
            paste_x = (target_width - new_width) // 2
            paste_y = (target_height - new_height) // 2
            result.paste(resized, (paste_x, paste_y))
            return result

        crop_x = (new_width - target_width) // 2
        crop_y = (new_height - target_height) // 2
        return resized.crop(
            (crop_x, crop_y, crop_x + target_width, crop_y + target_height)
        )

    def apply_gamma(
        self, img: Image.Image, gamma: float = 2.2
    ) -> Image.Image:
        """
        Applies gamma correction to an image.
        """
        if img.mode != "RGB":
            img = img.convert("RGB")
        np_img = np.array(img, dtype=np.uint8)
        # Use a temporary converter to avoid affecting global state
        temp_converter = ColorConverter(gamma=gamma)
        corrected = temp_converter._gamma_lut[np_img]
        return Image.fromarray(corrected, "RGB")


# --- General Purpose Utilities ---


def get_ip_address() -> str:
    """
    Tries to determine the local IP address by connecting to an external server
    Returns "IP not found" if unsuccessful.
    """
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.settimeout(2.0)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
    except (socket.timeout, OSError) as e:
        log.warning("Could not get IP address: %s", e)
        ip = "IP not found"
    finally:
        s.close()
    return ip


def draw_text(
    draw: ImageDraw.ImageDraw,
    text: str,
    font: ImageFont.FreeTypeFont | ImageFont.ImageFont,
    x: Union[int, str],
    y: Union[int, str],
    width: int,
    height: int,
    color: Tuple[int, int, int],
    padding: int = 5,
) -> Tuple[int, int, int, int]:
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
    # Get the actual bounding box of the text using ImageDraw.textbbox
    actual_bbox = draw.textbbox((0, 0), text, font=font)

    if actual_bbox is None:
        # Text is empty or completely transparent, return a zero-sized bbox
        return (0, 0, 0, 0)

    text_width = actual_bbox[2] - actual_bbox[0]
    text_height = actual_bbox[3] - actual_bbox[1]

    # Calculate X coordinate
    if isinstance(x, str):
        if x == "left":
            final_x = padding - actual_bbox[0]  # Adjust for textbbox offset
        elif x == "center":
            final_x = (width - text_width) // 2 - actual_bbox[0]
        elif x == "right":
            final_x = width - text_width - padding - actual_bbox[0]
        else:
            log.warning(
                f"Invalid keyword for x: '{x}'. Defaulting to 'left'."
            )
            final_x = padding - actual_bbox[0]
    else:
        final_x = x - actual_bbox[0]  # Adjust for textbbox offset

    # Calculate Y coordinate
    if isinstance(y, str):
        if y == "top":
            final_y = padding - actual_bbox[1]  # Adjust for textbbox offset
        elif y == "center":
            final_y = (height - text_height) // 2 - actual_bbox[1]
        elif y == "bottom":
            final_y = height - text_height - padding - actual_bbox[1]
        else:
            log.warning(f"Invalid keyword for y: '{y}'. Defaulting to 'top'.")
            final_y = padding - actual_bbox[1]
    else:
        final_y = y - actual_bbox[1]  # Adjust for textbbox offset

    final_pos = (final_x, final_y)

    # Draw the text on the actual draw object
    draw.text(final_pos, text, font=font, fill=color)

    # Return the bounding box of the drawn text for dirty region tracking
    # Expand by 1 pixel on right and bottom for robustness against anti-aliasing
    return (
        int(final_pos[0] + actual_bbox[0]),
        int(final_pos[1] + actual_bbox[1]),
        int(final_pos[0] + actual_bbox[2] + 1),
        int(final_pos[1] + actual_bbox[3] + 1),
    )
