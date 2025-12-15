#
# (c) 2025 Yoichi Tanibayashi
#
"""Display image command."""

import sys
import time

import click
from PIL import Image

from .. import ST7789V, __version__, click_common_opts
from ..utils.mylogger import errmsg, get_logger
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
@click.option(
    "--rst", type=int, default=25, show_default=True, help="RST PIN"
)
@click.option("--dc", type=int, default=24, show_default=True, help="DC PIN")
@click.option("--bl", type=int, default=23, show_default=True, help="BL PIN")
@click.option("--svg", is_flag=True, help="SVG flag")
@click_common_opts(__version__)
def image(ctx, image_path, duration, rst, dc, bl, svg, debug):
    """Displays an image with optional gamma correction.

    IMAGE_PATH: Path to the image file to display.
    """
    import cairosvg

    __log = get_logger(__name__, debug)
    __log.debug(
        "image_path=%s, duration=%s, svg=%s", image_path, duration, svg
    )
    __log.debug("rst=%s, dc=%s, bl=%s", rst, dc, bl)

    cmd_name = ctx.command.name
    __log.debug("cmd_name=%s", cmd_name)

    __log.info("Attempting to display image: %s", image_path)

    try:
        if svg:
            # png_data = cairosvg.svg2png(url=image_path)
            # source_image = Image.open(io.BytesIO(png_data))
            svg_file = image_path + ".svg"
            cairosvg.svg2png(url=image_path, write_to=svg_file)
            source_image = Image.open(svg_file)
        else:
            source_image = Image.open(image_path)
    except FileNotFoundError:
        __log.error("Error: Image file %a  not found.", image_path)
        sys.exit(1)
    except Exception as e:
        __log.error("Error opening image %s: %s", image_path, errmsg(e))
        sys.exit(1)

    processor = ImageProcessor()

    try:
        with ST7789V(pin={"rst": rst, "dc": dc, "bl": bl}) as lcd:
            __log.info(
                "Displaying original image resized to screen (contain mode)..."
            )

            # Resize while maintaining aspect ratio
            resized_image = processor.resize_with_aspect_ratio(
                source_image,
                lcd.size["width"],
                lcd.size["height"],
                fit_mode="contain",
            )
            lcd.display(resized_image)
            time.sleep(duration)

            for gamma in (1.0, 1.5, 1.0, 0.5, 1.0):
                __log.info("Applying gamma=%s", gamma)
                corrected_image = processor.apply_gamma(
                    resized_image, gamma=gamma
                )
                lcd.display(corrected_image)
                time.sleep(duration)

    except RuntimeError as e:
        __log.error(errmsg(e))
        sys.exit(1)
    except Exception as e:
        __log.error(errmsg(e))
        sys.exit(1)
    finally:
        __log.info("Image display finished.")
