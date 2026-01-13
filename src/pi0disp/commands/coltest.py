#
# (c) 2025 Yoichi Tanibayashi
#
"""Interactive color test subcommand."""

import atexit
import math
import os
import re
import readline

import click
import numpy as np
from PIL import Image, ImageDraw

from .. import __version__, click_common_opts, get_logger
from ..disp.disp_spi import SpiPins
from ..disp.st7789v import ST7789V

__log = get_logger(__name__)


class Coltest:
    """Coltest session manager."""

    HIST_FILE = os.path.expanduser("~/.color-test-history")
    CMD_RE = re.compile(r"(r|g|b|bl)(\d+)")

    def __init__(self, lcd, log_obj):
        """Constructor."""
        self.lcd = lcd
        self.log = log_obj
        self.r = 255
        self.g = 255
        self.b = 255
        self.bl = 255

    def setup_history(self):
        """Setup persistent history."""
        if os.path.exists(self.HIST_FILE):
            try:
                readline.read_history_file(self.HIST_FILE)
            except Exception as e:
                self.log.debug("Failed to read history file: %s", e)

        if hasattr(readline, "set_auto_history"):
            readline.set_auto_history(True)

        atexit.register(self.save_history)

    def save_history(self):
        """Save history to file."""
        try:
            readline.write_history_file(self.HIST_FILE)
        except Exception as e:
            self.log.debug("Failed to write history file: %s", e)

    def generate_image(self):
        """Generates a test image based on current state."""
        width = self.lcd.size.width
        height = self.lcd.size.height

        # 1. Start with a solid white background
        img_np = np.full((height, width, 3), 255, dtype=np.uint8)

        # 2. Define central black canvas (80% of screen)
        canvas_w = int(width * 0.8)
        canvas_h = int(height * 0.8)
        offset_x = (width - canvas_w) // 2
        offset_y = (height - canvas_h) // 2
        img_np[offset_y : offset_y + canvas_h, offset_x : offset_x + canvas_w] = 0

        # 3. Create layers for R, G, B circles within the canvas area
        radius = int(min(canvas_w / 3.5, canvas_h / 3.299))
        radius = max(1, radius)

        c_center_x = canvas_w // 2
        s = radius * 1.2
        c_center_y = int(canvas_h // 2 + s / (4 * math.sqrt(3)))

        # Define circle positions relative to canvas
        positions = [
            (int(c_center_x), int(c_center_y - s / math.sqrt(3))),  # R
            (
                int(c_center_x - s / 2),
                int(c_center_y + s / (2 * math.sqrt(3))),
            ),  # G
            (
                int(c_center_x + s / 2),
                int(c_center_y + s / (2 * math.sqrt(3))),
            ),  # B
        ]

        # Combine circle layers
        layers = np.zeros((canvas_h, canvas_w, 3), dtype=np.uint16)
        for i, (val, pos) in enumerate(zip([self.r, self.g, self.b], positions)):
            mask_img = Image.new("L", (canvas_w, canvas_h), 0)
            ImageDraw.Draw(mask_img).ellipse(
                (
                    pos[0] - radius,
                    pos[1] - radius,
                    pos[0] + radius,
                    pos[1] + radius,
                ),
                fill=255,
            )
            layers[:, :, i] = (np.array(mask_img).astype(np.uint16) * val) // 255

        combined = np.clip(layers, 0, 255).astype(np.uint8)
        img_np[offset_y : offset_y + canvas_h, offset_x : offset_x + canvas_w] = (
            combined
        )
        return Image.fromarray(img_np, "RGB")

    def print_help(self):
        """Print help message."""
        click.echo("Commands:")
        click.echo("  r<val>   - Set Red intensity (0-255)")
        click.echo("  g<val>   - Set Green intensity (0-255)")
        click.echo("  b<val>   - Set Blue intensity (0-255)")
        click.echo("  bl<val>  - Set Backlight brightness (0-255)")
        click.echo("  q        - Quit")
        click.echo("  e.g., 'r255 g128 bl64'")

    def run(self):
        """Run the interactive session."""
        self.setup_history()
        self.print_help()
        self.lcd.display(self.generate_image())

        while True:
            try:
                line = input("cmd> ").strip().lower()
                if not line:
                    continue
                if line == "q":
                    break

                updated = False
                for token in line.split():
                    match = self.CMD_RE.match(token)
                    if not match:
                        click.echo(f"Unknown command token: {token}")
                        continue

                    cmd, val_str = match.groups()
                    val = max(0, min(255, int(val_str)))

                    if cmd == "r":
                        self.r = val
                        updated = True
                    elif cmd == "g":
                        self.g = val
                        updated = True
                    elif cmd == "b":
                        self.b = val
                        updated = True
                    elif cmd == "bl":
                        self.bl = val
                        self.lcd.set_brightness(self.bl)
                        click.echo(f"Backlight set to {self.bl}")

                if updated:
                    self.lcd.display(self.generate_image())
                    click.echo(f"Updated: R={self.r}, G={self.g}, B={self.b}")

            except (EOFError, KeyboardInterrupt):
                click.echo("\nQuitting...")
                break
            except Exception as e:
                click.echo(f"Error: {e}")


@click.command(help="Interactive Color Test")
@click.option("--rst", type=int, default=25, show_default=True, help="RST PIN")
@click.option("--dc", type=int, default=24, show_default=True, help="DC PIN")
@click.option("--bl", type=int, default=23, show_default=True, help="BL PIN")
@click_common_opts(__version__)
def coltest(ctx, rst, dc, bl, debug):
    """Interactively adjust RGB intensities and backlight brightness."""
    __log = get_logger(__name__, debug)
    __log.debug("rst=%s, dc=%s, bl=%s", rst, dc, bl)

    try:
        with ST7789V(
            pin=SpiPins(rst=rst, dc=dc, bl=bl), brightness=255, debug=debug
        ) as lcd:
            __log.debug("Display initialized: %sx%s", lcd.size.width, lcd.size.height)
            session = Coltest(lcd, __log)
            session.run()
    except Exception as e:
        __log.error(f"Error occurred: {e}")
        exit(1)
    finally:
        click.echo("Done.")
