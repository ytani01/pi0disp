#
# (c) 2025 Yoichi Tanibayashi
#
"""Display RGB color circles command."""
import time
import numpy as np
from PIL import Image, ImageDraw
import click

from ..disp.st7789v import ST7789V
from ..utils.my_logger import get_logger

log = get_logger(__name__)

def generate_rgb_circles(width, height, colors_tuple):
    """Generates an image with three overlapping RGB circles using additive blending."""
    # Create a black background NumPy array
    final_image_np = np.zeros((height, width, 3), dtype=np.uint8)

    # Calculate optimal radius to fit the screen
    # Based on analysis:
    # Total width occupied: s + 2 * radius = 1.5 * radius + 2 * radius = 3.5 * radius
    # Total height occupied: (sqrt(3) * s / 2) + 2 * radius = (sqrt(3) * 1.5 * radius / 2) + 2 * radius approx 3.299 * radius
    # So, radius <= width / 3.5 and radius <= height / 3.299
    radius = int(min(width / 3.5, height / 3.299))

    # Ensure radius is at least 1 to avoid division by zero or negative values
    if radius < 1:
        radius = 1

    center_x = width // 2
    
    # Calculate side length of equilateral triangle
    s = radius * 1.2

    # Calculate the vertical offset to center the entire circle arrangement
    # The vertical extent of the circles is from (center_y - s / np.sqrt(3) - radius) to (center_y + s / (2 * np.sqrt(3)) + radius)
    # The midpoint of this extent is center_y - s / (4 * np.sqrt(3))
    # We want this midpoint to be height // 2
    # So, new_center_y = height // 2 + s / (4 * np.sqrt(3))
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
        draw.ellipse((pos[0] - radius, pos[1] - radius,
                      pos[0] + radius, pos[1] + radius),
                     fill=color)
        return np.array(img, dtype=np.uint8)

    # Draw each circle and add its pixel values to the final image
    red_circle_np = draw_opaque_circle(colors_tuple[0], red_pos, radius, width, height)
    green_circle_np = draw_opaque_circle(colors_tuple[1], green_pos, radius, width, height)
    blue_circle_np = draw_opaque_circle(colors_tuple[2], blue_pos, radius, width, height)

    # Add the arrays, clamping values at 255
    final_image_np = np.clip(final_image_np + red_circle_np, 0, 255)
    final_image_np = np.clip(final_image_np + green_circle_np, 0, 255)
    final_image_np = np.clip(final_image_np + blue_circle_np, 0, 255)

    return Image.fromarray(final_image_np, "RGB")

@click.command()
@click.option('--duration', '-d', type=float, default=5.0, help='Duration to display the image in seconds.')
def rgb(duration):
    """Displays RGB color circles with additive blending."""
    log.info("Initializing ST7789V display for color circles...")
    try:
        with ST7789V() as lcd:
            log.info(f"Display initialized: {lcd.width}x{lcd.height}")
            
            color_permutations = [
                ((255, 0, 0), (0, 255, 0), (0, 0, 255)),  # R, G, B
                ((0, 255, 0), (0, 0, 255), (255, 0, 0)),  # G, B, R
                ((0, 0, 255), (255, 0, 0), (0, 255, 0)),  # B, R, G
            ]

            log.info("Starting RGB color cycle...")
            while True:
                for colors_tuple in color_permutations:
                    log.info(f"Generating RGB circles image with colors: {colors_tuple}")
                    rgb_circles_image = generate_rgb_circles(lcd.width, lcd.height, colors_tuple)
                    
                    # Save the generated image to a file (optional, for debugging/screenshot)
                    output_filename = "rgb_circles_command.png"
                    rgb_circles_image.save(output_filename)
                    log.info(f"RGB circles image saved to {output_filename}")
                    
                    log.info(f"Displaying RGB circles for {duration} seconds...")
                    lcd.display(rgb_circles_image)
                    time.sleep(duration)

    except RuntimeError as e:
        log.error(f"Error: {e}. Make sure pigpio daemon is running and SPI is enabled.")
        exit(1)
    except Exception as e:
        log.error(f"An unexpected error occurred: {e}")
        exit(1)
    finally:
        log.info("Color circles display finished.")
