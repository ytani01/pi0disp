#!/usr/bin/env python3
#
# (c) 2025 Yoichi Tanibayashi
#
"""
color-test.py: pi0disp sample application.
Interactively adjust RGB intensities and backlight brightness.
"""

import math
import re
import sys

import numpy as np
from PIL import Image, ImageDraw

from pi0disp.disp.st7789v import ST7789V


def generate_test_image(width, height, r, g, b):
    """
    Generates a test image with a white background and a black central canvas,
    containing three overlapping additive circles (R, G, B).
    """
    # 1. Start with a solid white background
    img_np = np.full((height, width, 3), 255, dtype=np.uint8)

    # 2. Define central black canvas (80% of screen)
    canvas_w = int(width * 0.8)
    canvas_h = int(height * 0.8)
    offset_x = (width - canvas_w) // 2
    offset_y = (height - canvas_h) // 2

    # Fill canvas with black
    img_np[offset_y : offset_y + canvas_h, offset_x : offset_x + canvas_w] = 0

    # 3. Create layers for R, G, B circles within the canvas area
    # Rectangle size within canvas (approx 60% of canvas)
    radius = int(min(canvas_w / 3.5, canvas_h / 3.299))
    if radius < 1:
        radius = 1

    c_center_x = canvas_w // 2
    s = radius * 1.2
    c_center_y = int(canvas_h // 2 + s / (4 * math.sqrt(3)))

    def draw_circle_layer(color_idx, val, pos, rad, w, h):
        # Create a single channel layer using uint16 to prevent overflow
        layer = np.zeros((h, w, 3), dtype=np.uint16)
        mask_img = Image.new("L", (w, h), 0)
        draw = ImageDraw.Draw(mask_img)
        draw.ellipse(
            (pos[0] - rad, pos[1] - rad, pos[0] + rad, pos[1] + rad),
            fill=255,
        )
        mask_np = np.array(mask_img)
        # Apply intensity
        layer[:, :, color_idx] = (mask_np.astype(np.uint16) * val) // 255
        return layer

    # Red (top), Green (bottom-left), Blue (bottom-right)
    red_pos = (int(c_center_x), int(c_center_y - s / math.sqrt(3)))
    green_pos = (
        int(c_center_x - s / 2),
        int(c_center_y + s / (2 * math.sqrt(3))),
    )
    blue_pos = (
        int(c_center_x + s / 2),
        int(c_center_y + s / (2 * math.sqrt(3))),
    )

    r_layer = draw_circle_layer(0, r, red_pos, radius, canvas_w, canvas_h)
    g_layer = draw_circle_layer(1, g, green_pos, radius, canvas_w, canvas_h)
    b_layer = draw_circle_layer(2, b, blue_pos, radius, canvas_w, canvas_h)

    # 4. Additive blending
    combined_layers = r_layer + g_layer + b_layer
    combined_layers = np.clip(combined_layers, 0, 255).astype(np.uint8)

    # 5. Place the combined rectangles onto the black canvas
    img_np[offset_y : offset_y + canvas_h, offset_x : offset_x + canvas_w] = (
        combined_layers
    )

    return Image.fromarray(img_np, "RGB")


def print_help():
    print("Commands:")
    print("  r<val>   - Set Red intensity (0-255)")
    print("  g<val>   - Set Green intensity (0-255)")
    print("  b<val>   - Set Blue intensity (0-255)")
    print("  bl<val>  - Set Backlight brightness (0-255)")
    print("  q        - Quit")
    print(
        "  Multiple commands can be space-separated: e.g., 'r255 g128 bl64'"
    )


def main():
    # Initial state
    r_val, g_val, b_val = 255, 255, 255
    bl_val = 255

    print("Initializing display...")
    try:
        # Default pins for ST7789V as refactored
        with ST7789V(brightness=bl_val) as lcd:
            print(f"Display initialized: {lcd.size.width}x{lcd.size.height}")
            print_help()

            # Initial draw
            img = generate_test_image(
                lcd.size.width, lcd.size.height, r_val, g_val, b_val
            )
            lcd.display(img)

            while True:
                try:
                    line = sys.stdin.readline()
                    if not line:
                        break

                    line = line.strip().lower()
                    if not line:
                        continue

                    if line == "q":
                        break

                    tokens = line.split()
                    updated = False

                    for token in tokens:
                        # Match command (r, g, b, bl) and value
                        match = re.match(r"(r|g|b|bl)(\d+)", token)
                        if match:
                            cmd = match.group(1)
                            val = int(match.group(2))
                            val = max(0, min(255, val))

                            if cmd == "r":
                                r_val = val
                                updated = True
                            elif cmd == "g":
                                g_val = val
                                updated = True
                            elif cmd == "b":
                                b_val = val
                                updated = True
                            elif cmd == "bl":
                                bl_val = val
                                lcd.set_brightness(bl_val)
                                print(f"Backlight set to {bl_val}")
                        else:
                            print(f"Unknown command token: {token}")

                    if updated:
                        img = generate_test_image(
                            lcd.size.width,
                            lcd.size.height,
                            r_val,
                            g_val,
                            b_val,
                        )
                        lcd.display(img)
                        print(
                            f"Circles updated: R={r_val}, G={g_val}, B={b_val}"
                        )

                except EOFError:
                    break
                except KeyboardInterrupt:
                    print("\nQuitting...")
                    break
                except Exception as e:
                    print(f"Error: {e}")

    except Exception as e:
        print(f"Failed to initialize display: {e}")
        sys.exit(1)

    print("Done.")


if __name__ == "__main__":
    main()
