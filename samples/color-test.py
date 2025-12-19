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

from PIL import Image, ImageDraw

from pi0disp.disp.st7789v import ST7789V


def generate_rgb_circles(width, height, r, g, b):
    """Generates an image with three overlapping circles on a white background."""
    # Create white background RGBA image
    img = Image.new("RGBA", (width, height), (255, 255, 255, 255))

    # Create transparent overlay for circles
    overlay = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # Based on src/pi0disp/commands/rgb.py
    radius = int(min(width / 3.5, height / 3.299))
    if radius < 1:
        radius = 1

    center_x = width // 2
    s = radius * 1.2
    center_y = int(height // 2 + s / (4 * math.sqrt(3)))

    # Red (top), Green (bottom-left), Blue (bottom-right)
    red_pos = (int(center_x), int(center_y - s / math.sqrt(3)))
    green_pos = (
        int(center_x - s / 2),
        int(center_y + s / (2 * math.sqrt(3))),
    )
    blue_pos = (int(center_x + s / 2), int(center_y + s / (2 * math.sqrt(3))))

    # Draw circles with alpha based on intensities
    draw.ellipse(
        (
            red_pos[0] - radius,
            red_pos[1] - radius,
            red_pos[0] + radius,
            red_pos[1] + radius,
        ),
        fill=(255, 0, 0, r),
    )
    draw.ellipse(
        (
            green_pos[0] - radius,
            green_pos[1] - radius,
            green_pos[0] + radius,
            green_pos[1] + radius,
        ),
        fill=(0, 255, 0, g),
    )
    draw.ellipse(
        (
            blue_pos[0] - radius,
            blue_pos[1] - radius,
            blue_pos[0] + radius,
            blue_pos[1] + radius,
        ),
        fill=(0, 0, 255, b),
    )

    # Composite overlay on white background
    combined = Image.alpha_composite(img, overlay)

    return combined.convert("RGB")


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
            img = generate_rgb_circles(
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
                        img = generate_rgb_circles(
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
