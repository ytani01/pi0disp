#
# (c) 2026 Yoichi Tanibayashi
#
"""LCD Test Pattern drawing utility."""

import os

from PIL import Image, ImageDraw, ImageFont


def get_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Finds a font from the system and returns it."""
    font_paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/freefont/FreeMonoBold.ttf",
    ]
    for path in font_paths:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
    return ImageFont.load_default()


def draw_lcd_test_pattern(
    width: int,
    height: int,
    invert: bool,
    bgr: bool,
    index: int = 0,
    total: int = 0,
) -> Image.Image:
    """
    Draws a test pattern for LCD verification.

    Args:
        width: Display width.
        height: Display height.
        invert: Current invert setting.
        bgr: Current BGR setting.
        index: Current test index.
        total: Total number of tests.

    Returns:
        A PIL Image object containing the test pattern.
    """
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    # Background
    draw.rectangle([0, 0, width, height], fill="black")

    # Color bands
    bh = height // 8
    draw.rectangle([0, 0, width, bh], fill="#FF0000")
    draw.rectangle([0, bh, width, bh * 2], fill="#00FF00")
    draw.rectangle([0, bh * 2, width, bh * 3], fill="#0000FF")

    # Text settings
    f_mid = get_font(20)
    f_sm = get_font(16)

    # Display settings near center
    y_offset = bh * 3 + 15
    if total > 0:
        draw.text(
            (15, y_offset), f"TEST {index}/{total}", fill="white", font=f_mid
        )
        y_offset += 30

    conf_text = f"inv={invert}, bgr={bgr}"
    draw.text((15, y_offset), conf_text, fill="cyan", font=f_mid)

    # Guide at bottom
    draw.text(
        (15, height - 55), "If R/G/B & Black look OK,", fill="gray", font=f_sm
    )
    draw.text(
        (15, height - 35),
        "Use these values in TOML.",
        fill="yellow",
        font=f_sm,
    )

    return img
