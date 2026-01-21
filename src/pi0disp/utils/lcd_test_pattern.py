#
# (c) 2026 Yoichi Tanibayashi
#
"""LCD Test Pattern drawing utility."""

import os

from PIL import Image, ImageDraw, ImageFont

#
# Valid options for LCD Wizard
#
WIZARD_COLORS = {
    "red": "Red (Bright Red)",
    "blue": "Blue (Bright Blue)",
    "cyan": "Cyan (Bright Light Blue / Inverse of Red)",
    "yellow": "Yellow (Bright Yellow / Inverse of Blue)",
    "other": "Other / Unknown",
}

WIZARD_BG = {
    "black": "Black (Dark / Normal)",
    "white": "White (Bright / Inverted)",
}


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


def determine_lcd_settings(
    current_bgr: bool,
    current_invert: bool,
    seen_color: str,
    seen_bg: str,
) -> tuple[bool, bool]:
    """
    Determines the correct BGR and Invert settings based on user observation.

    Args:
        current_bgr: The BGR setting used when generating the pattern.
        current_invert: The Invert setting used when generating the pattern.
        seen_color: The color seen by the user at the top-left block.
                    ("red", "blue", "cyan", "yellow", etc.)
        seen_bg: The background color seen by the user.
                 ("black", "white")

    Returns:
        A tuple of (correct_bgr, correct_invert).

    Raises:
        ValueError: If the seen_color or seen_bg is invalid.
    """
    seen_color = seen_color.lower()
    seen_bg = seen_bg.lower()

    # 1. Determine "Is inverted?" based on background
    # If software is NOT inverting, and user sees black -> Panel is normal (Inv:Off)
    # If software is NOT inverting, and user sees white -> Panel is inverted (Inv:On)
    # If software IS inverting, and user sees black -> Panel is inverted (Inv:On)
    # If software IS inverting, and user sees white -> Panel is normal (Inv:Off)
    is_panel_inverted = (seen_bg == "white") ^ current_invert

    # 2. Determine "Is BGR?" based on top-left color
    # (Simplified logic: we assume the source was 'Red')
    # If user sees 'Cyan' or 'Yellow', we first undo the inversion in our mind.
    # Cyan (0, 255, 255) -> Inverted Red
    # Yellow (255, 255, 0) -> Inverted Blue
    
    color_without_inv = seen_color
    if seen_bg == "white":
        if seen_color == "cyan":
            color_without_inv = "red"
        elif seen_color == "yellow":
            color_without_inv = "blue"
        elif seen_color == "white":
            color_without_inv = "black"
        elif seen_color == "black":
            color_without_inv = "white"

    if color_without_inv not in ["red", "blue"]:
        raise ValueError(f"Unexpected color seen: {seen_color} (bg: {seen_bg})")

    # If we see Red when we expect Red (current_bgr=False) -> Panel is RGB
    # If we see Blue when we expect Red (current_bgr=False) -> Panel is BGR
    is_panel_bgr = (color_without_inv == "blue") ^ current_bgr

    return is_panel_bgr, is_panel_inverted


def draw_orientation_pattern(
    width: int,
    height: int,
    rotation: int,
) -> Image.Image:
    """
    Draws a test pattern for LCD orientation verification.
    Displays a large arrow and "UP" text, scaled to fit the screen.

    Args:
        width: Display width.
        height: Display height.
        rotation: Current rotation angle (0, 90, 180, 270).

    Returns:
        A PIL Image object containing the orientation pattern.
    """
    img = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(img)

    # 1. Scaling calculation
    # Use 80% of the smaller dimension as our base "unit"
    base_size = min(width, height) * 0.8
    
    # 2. Get font
    # "UP" text size should be about 1/4 of base_size
    font_size = int(base_size / 4)
    font = get_font(font_size)

    # 3. Draw Arrow
    # Arrow should point "Up" relative to the current rotation.
    # We draw it at the center.
    cx, cy = width // 2, height // 2
    
    # Arrow path (pointing Up)
    #   A (top)
    #  / \
    # B---C
    #   |
    #   D
    
    # Lengths
    head_h = base_size * 0.3
    head_w = base_size * 0.4
    stem_h = base_size * 0.4
    stem_w = base_size * 0.1
    
    # Vertices (relative to center)
    # Since we want to display "Up", and the LCD itself might be rotated,
    # we just draw a static "Up" arrow on the image. 
    # The image will be rotated by the driver later, or we can rotate it here.
    # In 'lcd-check --wizard', the user's task is to find the rotation where 
    # THIS arrow points to the physical top of the device.
    
    # Coordinates for an "Up" arrow
    points = [
        (cx, cy - base_size / 2),                     # Top point
        (cx - head_w / 2, cy - base_size / 2 + head_h), # Left head
        (cx - stem_w / 2, cy - base_size / 2 + head_h), # Left shoulder
        (cx - stem_w / 2, cy + base_size / 2 - font_size), # Bottom left
        (cx + stem_w / 2, cy + base_size / 2 - font_size), # Bottom right
        (cx + stem_w / 2, cy - base_size / 2 + head_h), # Right shoulder
        (cx + head_w / 2, cy - base_size / 2 + head_h), # Right head
    ]
    
    draw.polygon(points, fill="white", outline="cyan")
    
    # 4. Draw "UP" text below the arrow
    text = "UP"
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((cx - tw / 2, cy + base_size / 2 - th), text, fill="yellow", font=font)

    # 5. Corner markers (to help identify boundaries)
    m_size = 10
    draw.rectangle([0, 0, m_size, m_size], fill="red") # Top-Left
    draw.rectangle([width - m_size, 0, width, m_size], fill="green") # Top-Right
    draw.rectangle([0, height - m_size, m_size, height], fill="blue") # Bottom-Left
    draw.rectangle([width - m_size, height - m_size, width, height], fill="white") # Bottom-Right

    return img
