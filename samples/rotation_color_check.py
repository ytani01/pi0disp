#!/usr/bin/env python3
#
# (c) 2025 Yoichi Tanibayashi
#
"""
Rotation and Color Check Sample for pi0disp.
Displays color bars, gradients, and shapes to verify rotation and color reproduction.
"""

import time

from PIL import Image, ImageDraw, ImageFont

from pi0disp.disp.st7789v import ST7789V


def create_test_pattern(width, height, rotation):
    """Create a rich color test image for the given size and rotation."""
    image = Image.new("RGB", (width, height), "black")
    draw = ImageDraw.Draw(image)

    # 1. Color Bars (Top)
    bar_h = height // 8
    draw.rectangle([0, 0, width // 3, bar_h], fill="red")
    draw.rectangle([width // 3, 0, (width // 3) * 2, bar_h], fill="green")
    draw.rectangle([(width // 3) * 2, 0, width, bar_h], fill="blue")

    # 2. RGB Gradients (Middle)
    grad_h = height // 4
    y_start = bar_h + 10
    for x in range(width):
        r = int(x * 255 / width)
        draw.line([x, y_start, x, y_start + grad_h // 3], fill=(r, 0, 0))
        g = int(x * 255 / width)
        draw.line(
            [x, y_start + grad_h // 3, x, y_start + (grad_h // 3) * 2],
            fill=(0, g, 0),
        )
        b = int(x * 255 / width)
        draw.line(
            [x, y_start + (grad_h // 3) * 2, x, y_start + grad_h],
            fill=(0, 0, b),
        )

    # 3. Central Info Box
    center_x, center_y = width // 2, height // 2
    box_w, box_h = 160, 80
    draw.rectangle(
        [
            center_x - box_w // 2,
            center_y - box_h // 2,
            center_x + box_w // 2,
            center_y + box_h // 2,
        ],
        outline="white",
        fill=(40, 40, 40),
    )

    try:
        font = ImageFont.load_default()
    except Exception:
        font = None

    text_lines = [
        f"ROTATION: {rotation}",
        f"SIZE: {width}x{height}",
        "COLOR: RGB565",
    ]
    for i, line in enumerate(text_lines):
        draw.text(
            (center_x - 70, center_y - 30 + i * 20),
            line,
            fill="white",
            font=font,
        )

    # 4. Moving Corner Markers (Circles)
    r = 10
    draw.ellipse(
        [5, height - 25, 25, height - 5], fill="yellow"
    )  # Bottom-Left
    draw.text((30, height - 20), "B-L", fill="yellow")

    draw.ellipse(
        [width - 25, height - 25, width - 5, height - 5], fill="magenta"
    )  # Bottom-Right
    draw.text((width - 60, height - 20), "B-R", fill="magenta")

    # 5. Outer Border
    draw.rectangle([0, 0, width - 1, height - 1], outline="white", width=1)

    return image


def main():
    print("Starting Rotation & Color Check...")
    disp = ST7789V(debug=False)

    try:
        rotations = [0, 90, 180, 270]
        while True:  # Repeat indefinitely until Ctrl+C
            for rot in rotations:
                print(f"Rotation: {rot} deg")
                disp.set_rotation(rot)

                w, h = disp.size.width, disp.size.height
                image = create_test_pattern(w, h, rot)
                disp.display(image)

                time.sleep(3)

    except KeyboardInterrupt:
        print("\nStopped.")
    finally:
        disp.close()


if __name__ == "__main__":
    main()
