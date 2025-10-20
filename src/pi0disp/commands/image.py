#
# (c) 2025 Yoichi Tanibayashi
#
"""Display image command."""

import time

import click
from PIL import Image

from .. import ST7789V, __version__, click_common_opts, get_logger
from ..utils.utils import ImageProcessor


@click.command()
@click.argument(
    "image_path", type=click.Path(exists=True, dir_okay=False, readable=True)
)
@click.option(
    "--duration",
    "-s",
    type=float,
    default=3.0,
    show_default=True,
    help="Duration to display each image in seconds.",
)
@click_common_opts(__version__)
def image(ctx, image_path, duration, debug):
    """Displays an image with optional gamma correction.

    IMAGE_PATH: Path to the image file to display.
    """
    __log = get_logger(__name__, debug)
    __log.debug("image_path=%s, duration=%s", image_path, duration)

    cmd_name = ctx.command.name
    __log.debug("cmd_name=%s", cmd_name)

    __log.info(f"Attempting to display image: {image_path}")

    try:
        source_image = Image.open(image_path)
    except FileNotFoundError:
        __log.error(f"Error: Image file '{image_path}' not found.")
        exit(1)
    except Exception as e:
        __log.error(f"Error opening image '{image_path}': {e}")
        exit(1)

    processor = ImageProcessor()

    try:
        with ST7789V() as lcd:
            __log.info(
                "Displaying original image resized to screen (contain mode)..."
            )

            # Resize while maintaining aspect ratio
            resized_image = processor.resize_with_aspect_ratio(
                source_image, lcd.width, lcd.height, fit_mode="contain"
            )
            lcd.display(resized_image)
            time.sleep(duration)

            for gamma in (1.0, 1.5, 1.0, 0.5, 1.0):
                __log.info(f"Applying gamma={gamma}")
                corrected_image = processor.apply_gamma(
                    resized_image, gamma=gamma
                )
                lcd.display(corrected_image)
                time.sleep(duration)

    except RuntimeError as e:
        __log.error(
            f"Error: {e}. Make sure pigpio daemon is running and SPI is enabled."
        )
        exit(1)
    except Exception as e:
        __log.error(
            f"An unexpected error occurred during display processing: {e}"
        )
        exit(1)
    finally:
        __log.info("Image display finished.")
