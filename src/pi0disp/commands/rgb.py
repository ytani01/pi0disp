#
# (c) 2025 Yoichi Tanibayashi
#
"""Display RGB color circles command."""

import time
from typing import Tuple

import click
import numpy as np
from PIL import Image, ImageDraw

from .. import __version__, click_common_opts, get_logger
from ..disp.disp_spi import SpiPins
from ..disp.st7789v import ST7789V

__log = get_logger(__name__)


def generate_rgb_circles(
    width: int,
    height: int,
    colors_tuple: Tuple[
        Tuple[int, int, int], Tuple[int, int, int], Tuple[int, int, int]
    ],
) -> Image.Image:
    """Generates an image with three overlapping RGB circles using additive blending."""
    # Create a black background NumPy array
    final_image_np = np.zeros((height, width, 3), dtype=np.uint8)

    # Calculate optimal radius to fit the screen
    radius = int(min(width / 3.5, height / 3.299))

    # Ensure radius is at least 1 to avoid division by zero or negative values
    if radius < 1:
        radius = 1

    center_x = width // 2

    # Calculate side length of equilateral triangle
    s = radius * 1.2

    center_y = int(height // 2 + s / (4 * np.sqrt(3)))

    # Calculate coordinates for equilateral triangle vertices
    # Centroid of the triangle is effectively at (center_x, center_y) after adjustment
    # Red (top vertex)
    red_pos = (int(center_x), int(center_y - s / np.sqrt(3)))
    # Green (bottom-left vertex)
    green_pos = (int(center_x - s / 2), int(center_y + s / (2 * np.sqrt(3))))
    # Blue (bottom-right vertex)
    blue_pos = (int(center_x + s / 2), int(center_y + s / (2 * np.sqrt(3))))

    # Helper function to draw a single opaque circle on a black background
    def draw_opaque_circle(color, pos, radius, img_width, img_height):
        img = Image.new("RGB", (img_width, img_height), (0, 0, 0))
        draw = ImageDraw.Draw(img)
        draw.ellipse(
            (
                pos[0] - radius,
                pos[1] - radius,
                pos[0] + radius,
                pos[1] + radius,
            ),
            fill=color,
        )
        return np.array(img, dtype=np.uint8)

    # Draw each circle and add its pixel values to the final image
    for color, pos in zip(colors_tuple, [red_pos, green_pos, blue_pos]):
        circle_np = draw_opaque_circle(color, pos, radius, width, height)
        final_image_np = np.clip(final_image_np + circle_np, 0, 255)

    return Image.fromarray(final_image_np, "RGB")


@click.command(help="RGB Circles")
@click.option(
    "--duration",
    "-s",
    type=float,
    default=2.0,
    help="Duration to display the image in seconds.",
)
@click.option(
    "--rst", type=int, default=25, show_default=True, help="RST PIN"
)
@click.option("--dc", type=int, default=24, show_default=True, help="DC PIN")
@click.option("--bl", type=int, default=23, show_default=True, help="BL PIN")
@click_common_opts(__version__)
def rgb(ctx, duration, rst, dc, bl, debug):
    """Displays RGB color circles with additive blending."""
    __log = get_logger(__name__, debug)
    __log.debug("duration=%s", duration)
    __log.debug("rst=%s, dc=%s, bl=%s", rst, dc, bl)

    try:
        with ST7789V(pin=SpiPins(rst=rst, dc=dc, bl=bl), debug=debug) as lcd:
            __log.debug(
                "Display initialized: %sx%s",
                lcd.size.width,
                lcd.size.height,
            )

            color_permutations = [
                ((255, 0, 0), (0, 255, 0), (0, 0, 255)),  # R, G, B
                ((0, 255, 0), (0, 0, 255), (255, 0, 0)),  # G, B, R
                ((0, 0, 255), (255, 0, 0), (0, 255, 0)),  # B, R, G
            ]

            print("Starting RGB color cycle... Ctrl+C to stop.")
            while True:
                for colors_tuple in color_permutations:
                    __log.debug(
                        "Generating RGB circles image with colors: %s",
                        colors_tuple,
                    )
                    rgb_circles_image = generate_rgb_circles(
                        lcd.size.width, lcd.size.height, colors_tuple
                    )

                    # Save the generated image to a file (optional, for debugging)
                    if debug:
                        output_filename = "/tmp/rgb_circles_command.png"
                        rgb_circles_image.save(output_filename)
                        __log.debug(
                            "RGB circles image saved to %s", output_filename
                        )

                    __log.debug(
                        "Displaying RGB circles for %s seconds...", duration
                    )
                    lcd.display(rgb_circles_image)
                    time.sleep(duration)

    except KeyboardInterrupt:
        print("\nFinished.")
    except Exception as e:
        __log.error(f"Error occurred: {e}")
        exit(1)
