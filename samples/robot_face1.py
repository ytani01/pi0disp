#
# (c) 2025 Yoichi Tanibayashi
#
"""
Geometric robot face animation standalone sample with debug logging.

This script demonstrates how to draw a robot face using geometric shapes
and animate its expressions (e.g., blinking eyes) using partial updates.
"""
import time
import sys
from pathlib import Path
from typing import Tuple, Optional

import click
from PIL import Image, ImageDraw, ImageFont

# Add project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from pi0disp.disp.st7789v import ST7789V
from pi0disp.utils.my_logger import get_logger
from pi0disp.utils.utils import draw_text, merge_bboxes, expand_bbox

log = get_logger(__name__, debug=False) # Initialize with debug off by default

# --- Configuration ---
SPI_SPEED_HZ = 32_000_000
FONT_PATH = "../src/pi0disp/fonts/Firge-Regular.ttf" # Adjusted path
TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (0, 0, 0) # Black background

# --- Face Geometry (relative to display size) ---
EYE_RADIUS_RATIO = 0.18 # Slightly larger eyes
EYE_SPACING_RATIO = 0.5 # Widened eye spacing
EYE_Y_POS_RATIO = 0.4 # Moved eyes further down
MOUTH_WIDTH_RATIO = 0.3 # Slightly narrower mouth
MOUTH_HEIGHT_RATIO = 0.12 # Adjusted for better arc visibility
MOUTH_Y_POS_RATIO = 0.75 # Moved mouth further down

class RobotFace:
    """Manages drawing and animating the geometric robot face."""

    def __init__(self, lcd: ST7789V, font: ImageFont.FreeTypeFont | ImageFont.ImageFont):
        log.debug("RobotFace: Initializing...")
        self.lcd = lcd
        self.font = font
        self.width = lcd.width
        self.height = lcd.height
        self.base_image = Image.new(
            "RGB", (self.width, self.height), BACKGROUND_COLOR
        )
        self.draw = ImageDraw.Draw(self.base_image)

        # Calculate absolute positions and sizes
        self.eye_radius = int(self.width * EYE_RADIUS_RATIO)
        self.eye_spacing = int(self.width * EYE_SPACING_RATIO)
        self.eye_y = int(self.height * EYE_Y_POS_RATIO)

        self.left_eye_center_x = self.width // 2 - self.eye_spacing // 2
        self.right_eye_center_x = self.width // 2 + self.eye_spacing // 2

        self.mouth_width = int(self.width * MOUTH_WIDTH_RATIO)
        self.mouth_height = int(self.height * MOUTH_HEIGHT_RATIO)
        self.mouth_y = int(self.height * MOUTH_Y_POS_RATIO)
        self.mouth_x = (self.width - self.mouth_width) // 2

        # Base bboxes (unpadded)
        self.left_eye_base_bbox = self._get_eye_bbox(
            self.left_eye_center_x, self.eye_y, self.eye_radius
        )
        self.right_eye_base_bbox = self._get_eye_bbox(
            self.right_eye_center_x, self.eye_y, self.eye_radius
        )
        self.mouth_base_bbox = (
            self.mouth_x,
            self.mouth_y,
            self.mouth_x + self.mouth_width,
            self.mouth_y + self.mouth_height
        )

        # Track last drawn regions for precise clearing
        self.last_left_eye_drawn_bbox: Optional[
            Tuple[int, int, int, int]
        ] = None
        self.last_right_eye_drawn_bbox: Optional[
            Tuple[int, int, int, int]
        ] = None
        self.last_mouth_drawn_bbox: Optional[
            Tuple[int, int, int, int]
        ] = None
        self.last_text_drawn_bbox: Optional[
            Tuple[int, int, int, int]
        ] = None
        self.last_text_content: Optional[str] = None
        self.last_text_y_offset: Optional[int] = None
        log.debug("RobotFace: Initialization complete.")

    def _get_eye_bbox(
            self, center_x: int, center_y: int, radius: int
    ) -> Tuple[int, int, int, int]:
        return (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        )

    def _draw_overlay_text(
            self, text: str, y_offset_ratio: float = 0.0
    ) -> Tuple[int, int, int, int]:
        log.debug(
            "_draw_overlay_text: Drawing text '%s' at y_offset_ratio=%s",
            text, y_offset_ratio
        )
        draw = self.draw
        
        # Use the draw_text utility function directly to draw and get its precise bbox
        current_text_bbox = draw_text(
            draw,
            text,
            self.font,
            x="center",
            y=int(self.height * y_offset_ratio),
            width=self.width,
            height=self.height,
            color=TEXT_COLOR,
            padding=5 # Use the same padding as defined in draw_eyes for consistency
        )
        
        self.last_text_drawn_bbox = current_text_bbox
        self.last_text_content = text # Store content for clearing
        self.last_text_y_offset = int(self.height * y_offset_ratio)
        return current_text_bbox # Return the drawn region as dirty

    def _clear_overlay_text(self) -> Optional[Tuple[int, int, int, int]]:
        log.debug("_clear_overlay_text: Clearing any existing text.")
        if self.last_text_drawn_bbox and self.last_text_content is not None and self.last_text_y_offset is not None:
            draw = self.draw

            # First, draw a solid rectangle over the last drawn text area (expanded)
            # This is a brute-force clear to ensure no lingering pixels

            # Expand by 2 pixels
            solid_clear_bbox = expand_bbox(self.last_text_drawn_bbox, 2)
            draw.rectangle(solid_clear_bbox, fill=BACKGROUND_COLOR)

            # Then, draw the text again in the background color
            # to clear it with anti-aliasing
            cleared_bbox = draw_text(
                draw,
                self.last_text_content,
                self.font,
                x="center",
                y=self.last_text_y_offset,
                width=self.width,
                height=self.height,
                color=BACKGROUND_COLOR,
                padding=5
            )
            self.last_text_drawn_bbox = None
            self.last_text_content = None
            self.last_text_y_offset = None
            log.debug(f"_clear_overlay_text: Cleared region {cleared_bbox}")
            return cleared_bbox
        log.debug("_clear_overlay_text: No text to clear.")
        return None

    def draw_eyes(
            self,
            state: str = "open",
            color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Tuple[int, int, int, int]:
        log.debug(f"draw_eyes: Drawing eyes in state '{state}'")
        draw = self.draw
        
        # Define a padding for clearing to ensure no afterimages
        padding = 5
        
        # Calculate padded clear regions for both eyes as ellipses
        padded_left_eye_clear_ellipse_bbox = self._get_eye_bbox(
            self.left_eye_center_x, self.eye_y, self.eye_radius + padding
        )
        padded_right_eye_clear_ellipse_bbox = self._get_eye_bbox(
            self.right_eye_center_x, self.eye_y, self.eye_radius + padding
        )

        # Clear the padded elliptical regions for both eyes
        log.debug(f"draw_eyes: Clearing padded eye areas: {padded_left_eye_clear_ellipse_bbox}, {padded_right_eye_clear_ellipse_bbox}")
        draw.ellipse(padded_left_eye_clear_ellipse_bbox, fill=BACKGROUND_COLOR)
        draw.ellipse(padded_right_eye_clear_ellipse_bbox, fill=BACKGROUND_COLOR)

        # Initialize clear_region with the merged bounding boxes of the cleared ellipses
        clear_region = merge_bboxes(
            padded_left_eye_clear_ellipse_bbox, padded_right_eye_clear_ellipse_bbox
        )

        drawn_bboxes = []

        if state == "open":
            # Draw outer circle (white)
            draw.ellipse(self.left_eye_base_bbox, fill=color, outline=color)
            draw.ellipse(self.right_eye_base_bbox, fill=color, outline=color)
            drawn_bboxes.append(self.left_eye_base_bbox)
            drawn_bboxes.append(self.right_eye_base_bbox)

            # Draw inner circle (black) to create a hollow effect
            inner_radius = int(self.eye_radius * 0.6)
            left_inner_bbox = self._get_eye_bbox(
                self.left_eye_center_x, self.eye_y, inner_radius
            )
            right_inner_bbox = self._get_eye_bbox(
                self.right_eye_center_x, self.eye_y, inner_radius
            )
            draw.ellipse(left_inner_bbox, fill=BACKGROUND_COLOR)
            draw.ellipse(right_inner_bbox, fill=BACKGROUND_COLOR)
            drawn_bboxes.append(left_inner_bbox)
            drawn_bboxes.append(right_inner_bbox)

        elif state == "closed":
            # Draw a horizontal line for closed eyes
            line_y = self.eye_y
            line_width = int(self.eye_radius * 1.8) # Slightly less than full diameter
            
            # Left eye line
            left_line_start_x = self.left_eye_center_x - line_width // 2
            left_line_end_x = self.left_eye_center_x + line_width // 2
            draw.line(
                (left_line_start_x, line_y, left_line_end_x, line_y),
                fill=color, width=2
            )
            drawn_bboxes.append(
                (left_line_start_x, line_y - 1, left_line_end_x, line_y + 1)
            ) # Approximate bbox

            # Right eye line
            right_line_start_x = self.right_eye_center_x - line_width // 2
            right_line_end_x = self.right_eye_center_x + line_width // 2
            draw.line(
                (right_line_start_x, line_y, right_line_end_x, line_y),
                fill=color, width=2
            )
            drawn_bboxes.append(
                (right_line_start_x, line_y - 1, right_line_end_x, line_y + 1)
            ) # Approximate bbox

        elif state == "happy_eyes":
            # Filled eyes for happy expression
            draw.ellipse(self.left_eye_base_bbox, fill=color, outline=color)
            draw.ellipse(self.right_eye_base_bbox, fill=color, outline=color)
            drawn_bboxes.append(self.left_eye_base_bbox)
            drawn_bboxes.append(self.right_eye_base_bbox)

            # Add small black pupils
            pupil_radius = int(self.eye_radius * 0.2) # Smaller pupil
            left_pupil_bbox = self._get_eye_bbox(
                self.left_eye_center_x, self.eye_y, pupil_radius
            )
            right_pupil_bbox = self._get_eye_bbox(
                self.right_eye_center_x, self.eye_y, pupil_radius
            )
            draw.ellipse(left_pupil_bbox, fill=BACKGROUND_COLOR)
            draw.ellipse(right_pupil_bbox, fill=BACKGROUND_COLOR)
            drawn_bboxes.append(left_pupil_bbox)
            drawn_bboxes.append(right_pupil_bbox)

        elif state == "sad_eyes":
            # Eyes looking up/inward (by shifting inner black circle)
            inner_radius = int(self.eye_radius * 0.6)
            pupil_offset_x = 0
            pupil_offset_y = int(self.eye_radius * 0.3)
            
            draw.ellipse(self.left_eye_base_bbox, fill=color, outline=color)
            draw.ellipse(self.right_eye_base_bbox, fill=color, outline=color)
            drawn_bboxes.append(self.left_eye_base_bbox)
            drawn_bboxes.append(self.right_eye_base_bbox)
            
            left_pupil_bbox = self._get_eye_bbox(
                self.left_eye_center_x - pupil_offset_x,
                self.eye_y + pupil_offset_y,
                inner_radius
            )
            right_pupil_bbox = self._get_eye_bbox(
                self.right_eye_center_x + pupil_offset_x,
                self.eye_y + pupil_offset_y,
                inner_radius
            )
            draw.ellipse(left_pupil_bbox, fill=BACKGROUND_COLOR)
            draw.ellipse(right_pupil_bbox, fill=BACKGROUND_COLOR)
            drawn_bboxes.append(left_pupil_bbox)
            drawn_bboxes.append(right_pupil_bbox)

        elif state == "question_eyes":
            # Eyes looking up/outward (by shifting inner black circle)
            inner_radius = int(self.eye_radius * 0.6)
            pupil_offset_x = int(self.eye_radius * 0.2)
            pupil_offset_y = int(self.eye_radius * 0.2)
            
            draw.ellipse(self.left_eye_base_bbox, fill=color, outline=color)
            draw.ellipse(self.right_eye_base_bbox, fill=color, outline=color)
            drawn_bboxes.append(self.left_eye_base_bbox)
            drawn_bboxes.append(self.right_eye_base_bbox)
            
            left_pupil_bbox = self._get_eye_bbox(
                self.left_eye_center_x + pupil_offset_x,
                self.eye_y - pupil_offset_y,
                inner_radius
            )
            right_pupil_bbox = self._get_eye_bbox(
                self.right_eye_center_x - pupil_offset_x,
                self.eye_y - pupil_offset_y,
                inner_radius
            )
            draw.ellipse(left_pupil_bbox, fill=BACKGROUND_COLOR)
            draw.ellipse(right_pupil_bbox, fill=BACKGROUND_COLOR)
            drawn_bboxes.append(left_pupil_bbox)
            drawn_bboxes.append(right_pupil_bbox)

        # Add more eye states as needed
        self.current_eyes_state = state
        
        drawn_region = None
        for bbox in drawn_bboxes:
            drawn_region = merge_bboxes(drawn_region, bbox)

        self.last_left_eye_drawn_bbox = drawn_bboxes[0] if drawn_bboxes else None
        self.last_right_eye_drawn_bbox = drawn_bboxes[1] if len(drawn_bboxes) > 1 else None

        return merge_bboxes(
            clear_region, drawn_region
        ) or (0, 0, 0, 0) # Return the merged clear/drawn region as dirty

    def draw_mouth(
            self,
            state: str = "neutral",
            color: Tuple[int, int, int] = (255, 255, 255)
    ) -> Tuple[int, int, int, int]:
        log.debug(f"draw_mouth: Drawing mouth in state '{state}'")
        draw = self.draw
        
        # Calculate clear region: previous drawn bbox + current base bbox
        clear_region = merge_bboxes(
            self.last_mouth_drawn_bbox, self.mouth_base_bbox
        )

        if clear_region:
            log.debug(f"draw_mouth: Clearing region {clear_region}")
            draw.rectangle(clear_region, fill=BACKGROUND_COLOR)

        drawn_bbox = None

        if state == "neutral":
            # Use line_mouth for neutral
            line_length = int(self.mouth_width * 0.5) # Shorter dash for neutral mouth
            line_start_x = self.mouth_x + (self.mouth_width - line_length) // 2
            line_end_x = line_start_x + line_length
            line_y = self.mouth_y + self.mouth_height // 2
            draw.line((line_start_x, line_y, line_end_x, line_y), fill=color, width=4)
            drawn_bbox = (
                line_start_x, line_y - 1, line_end_x, line_y + 1
            ) # Approximate bbox for line

        elif state == "happy":
            # Adjust bbox for happy arc to ensure it's fully visible
            happy_arc_bbox = (
                self.mouth_x, self.mouth_y - self.mouth_height // 2, 
                self.mouth_x + self.mouth_width, self.mouth_y + self.mouth_height
            )
            # Draw a thick arc for a broader smile
            draw.arc(
                happy_arc_bbox, start=0, end=180, fill=color, width=4
            ) # Changed to arc, width=4
            drawn_bbox = happy_arc_bbox

        elif state == "sad":
            # Adjust bbox for sad arc to ensure it's fully visible
            sad_arc_bbox = (
                self.mouth_x,
                self.mouth_y, 
                self.mouth_x + self.mouth_width,
                int(self.mouth_y + self.mouth_height * 1.5)
            ) # Extend downwards
            draw.arc(sad_arc_bbox, start=180, end=360, fill=color, width=2)
            drawn_bbox = sad_arc_bbox

        elif state == "line_mouth":
            # This state is now redundant with "neutral" but kept for clarity
            line_length = int(self.mouth_width * 0.5) 
            line_start_x = self.mouth_x + (self.mouth_width - line_length) // 2
            line_end_x = line_start_x + line_length
            line_y = self.mouth_y + self.mouth_height // 2
            draw.line(
                (line_start_x, line_y, line_end_x, line_y),
                fill=color, width=4
            )
            drawn_bbox = (line_start_x, line_y - 1, line_end_x, line_y + 1)

        elif state == "question_mouth":
            # Draw a small dash for question
            dash_width = int(self.mouth_width * 0.2)
            dash_x = self.mouth_x + (self.mouth_width - dash_width) // 2
            line_y = self.mouth_y + self.mouth_height // 2
            draw.line(
                (dash_x, line_y, dash_x + dash_width, line_y),
                fill=color, width=2
            )
            drawn_bbox = (dash_x, line_y - 1, dash_x + dash_width, line_y + 1)

        # Add more mouth states as needed
        self.current_mouth_state = state
        self.last_mouth_drawn_bbox = drawn_bbox
        return merge_bboxes(
            clear_region, drawn_bbox
        ) or (0, 0, 0, 0) # Return the merged clear/drawn region as dirty

    def animate_blink(self, num_blinks: int = 1, blink_duration: float = 0.1):
        log.debug(f"animate_blink: Starting {num_blinks} blinks.")
        for _ in range(num_blinks):
            # Close eyes
            dirty_eyes = self.draw_eyes(state="closed")
            self.lcd.display_region(self.base_image, *dirty_eyes)
            time.sleep(blink_duration)

            # Open eyes
            dirty_eyes = self.draw_eyes(state="open")
            self.lcd.display_region(self.base_image, *dirty_eyes)
            time.sleep(blink_duration)
        log.debug("animate_blink: Blinks complete.")

    def animate_expression(
            self,
            expression: str,
            duration: float = 1.0,
            save_screenshot_flag: bool = False
    ):
        log.info(f"animate_expression: Changing to '{expression}' expression.")
        total_dirty_region = None

        # Clear any previous overlay text and merge its expanded bbox
        # into total_dirty_region
        cleared_text_bbox = self._clear_overlay_text()
        if cleared_text_bbox:
            expanded_cleared_bbox = expand_bbox(cleared_text_bbox, 2) # Revert to 2
            total_dirty_region = merge_bboxes(
                total_dirty_region, expanded_cleared_bbox
            )

        # Draw eyes and mouth, merging their dirty regions into total_dirty_region
        if expression == "happy":
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_eyes(state="happy_eyes")
            )
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_mouth(state="happy")
            )
        elif expression == "sad":
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_eyes(state="sad_eyes")
            )
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_mouth(state="sad")
            )
        elif expression == "neutral":
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_eyes(state="open")
            )
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_mouth(state="neutral")
            ) # Use "neutral" for line mouth
        elif expression == "question":
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_eyes(state="question_eyes")
            )
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_mouth(state="question_mouth")
            )
            # Draw overlay text and merge its dirty region
            total_dirty_region = merge_bboxes(
                total_dirty_region,
                self._draw_overlay_text("", y_offset_ratio=0.1)
            ) # Above head
        elif expression == "sleepy":
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_eyes(state="closed")
            )
            total_dirty_region = merge_bboxes(
                total_dirty_region, self.draw_mouth(state="neutral")
            ) # Neutral mouth for sleepy
            # Draw overlay text and merge its dirty region
            total_dirty_region = merge_bboxes(
                total_dirty_region,
                self._draw_overlay_text("zzz", y_offset_ratio=0.15)
            ) # Above eyes
        # Add more expressions

        # Update the display once with the total merged dirty region
        if total_dirty_region:
            log.debug(
                f"animate_expression: Displaying total dirty region {total_dirty_region}"
            )
            # Expand total_dirty_region for robustness
            expanded_dirty_region = expand_bbox(total_dirty_region, 2)
            self.lcd.display_region(self.base_image, *expanded_dirty_region)
            if save_screenshot_flag:
                self.save_screenshot(
                    f"screenshot_{expression}.png"
                ) # Save with expression name
        time.sleep(duration)
        log.debug(f"animate_expression: '{expression}' expression complete.")

    def save_screenshot(self, filename: str = "screenshot.png"):
        """Saves the current base_image (display buffer) to a PNG file."""
        try:
            self.base_image.save(filename)
            log.info(f"Screenshot saved to {filename}")
        except Exception as e:
            log.error(f"Failed to save screenshot to {filename}: {e}")

@click.command()
@click.option(
    '--screenshot', is_flag=True, default=False,
    help='Save screenshot for each expression.'
)
@click.option(
    '--face',
    type=click.Choice(
        ['neutral', 'happy', 'sad', 'question', 'sleepy'], case_sensitive=False
    ),
    help='Display a specific face and exit.'
)
@click.option(
    '--debug', is_flag=True, default=False, help='Enable debug logging.'
)
def main(screenshot, face, debug):
    """Main function to run the geometric robot face animation."""
    script_dir = Path(__file__).parent

    # Re-initialize the logger with the correct debug setting based on the CLI argument
    global log # Declare global to reassign the module-level log variable
    log = get_logger(__name__, debug=debug)

    log.info("Starting geometric robot face animation...")

    try:
        log.debug("main: Initializing ST7789V display.")
        with ST7789V(speed_hz=SPI_SPEED_HZ) as lcd:
            log.debug(
                "main: ST7789V display initialized. %s x %s",
                lcd.width, lcd.height
            )

            # Load font
            font_path_abs = script_dir / FONT_PATH
            log.debug(f"main: Loading font from {font_path_abs}")
            try:
                font = ImageFont.truetype(str(font_path_abs), 45)
                log.debug("main: Font loaded successfully.")
            except IOError:
                log.warning(
                    f"Font '{font_path_abs}' not found. Using default."
                )
                font = ImageFont.load_default()

            log.debug("main: Initializing RobotFace.")
            robot_face = RobotFace(lcd, font)
            log.debug("main: RobotFace initialized.")

            # Draw initial neutral face
            log.debug("main: Drawing initial neutral face.")
            robot_face.draw_eyes(state="open")
            robot_face.draw_mouth(state="neutral")
            lcd.display(robot_face.base_image)
            log.debug("main: Initial face displayed. Waiting 2 seconds.")
            time.sleep(2)

            if face:
                log.info(f"Displaying '{face}' expression.")
                robot_face.animate_expression(
                    face, duration=5.0, save_screenshot_flag=screenshot
                )
                log.info("Exiting.")
                return

            # Animation loop
            log.info("main: Starting animation loop. Press Ctrl+C to exit.")
            expressions = ["neutral", "happy", "sad", "question", "sleepy"]
            while True:
                for expression in expressions:
                    log.info(f"{expression.capitalize()} expression")
                    robot_face.animate_expression(
                        expression,
                        duration=2.0,
                        save_screenshot_flag=screenshot
                    )
                    robot_face.animate_blink(num_blinks=1, blink_duration=0.1)
                    time.sleep(1.0)

    except KeyboardInterrupt:
        log.info("\nExiting gracefully.")
    except Exception as e:
        log.error(f"An error occurred: {e}", exc_info=True)
        exit(1)

if __name__ == "__main__":
    main()
