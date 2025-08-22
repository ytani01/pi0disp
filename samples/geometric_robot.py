#
# (c) 2025 Yoichi Tanibayashi
#
"""
Geometric robot face animation standalone sample.

This script demonstrates how to draw a robot face using geometric shapes
and animate its expressions (e.g., blinking eyes) using partial updates.
"""
import time
import sys
from pathlib import Path
from typing import Tuple, Optional

from PIL import Image, ImageDraw, ImageFont

# Add project root to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from pi0disp import ST7789V, get_logger
from pi0disp.utils import draw_text, clamp_region, merge_bboxes

log = get_logger(__name__)

# --- Configuration ---
SPI_SPEED_HZ = 32_000_000
FONT_PATH = "../src/pi0disp/fonts/Firge-Regular.ttf" # Adjusted path
TEXT_COLOR = (255, 255, 255)
BACKGROUND_COLOR = (0, 0, 0) # Black background

# --- Face Geometry (relative to display size) ---
EYE_RADIUS_RATIO = 0.18 # Slightly larger eyes
EYE_SPACING_RATIO = 0.4 # Widened eye spacing
EYE_Y_POS_RATIO = 0.4 # Moved eyes further down
MOUTH_WIDTH_RATIO = 0.3 # Slightly narrower mouth
MOUTH_HEIGHT_RATIO = 0.12 # Adjusted for better arc visibility
MOUTH_Y_POS_RATIO = 0.75 # Moved mouth further down

class RobotFace:
    """Manages drawing and animating the geometric robot face."""

    def __init__(self, lcd: ST7789V, font: ImageFont.ImageFont):
        self.lcd = lcd
        self.font = font
        self.width = lcd.width
        self.height = lcd.height
        self.base_image = Image.new("RGB", (self.width, self.height), BACKGROUND_COLOR)
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
        self.left_eye_base_bbox = self._get_eye_bbox(self.left_eye_center_x, self.eye_y, self.eye_radius)
        self.right_eye_base_bbox = self._get_eye_bbox(self.right_eye_center_x, self.eye_y, self.eye_radius)
        self.mouth_base_bbox = (self.mouth_x, self.mouth_y, self.mouth_x + self.mouth_width, self.mouth_y + self.mouth_height)

        # Track last drawn regions for precise clearing
        self.last_left_eye_drawn_bbox: Optional[Tuple[int, int, int, int]] = None
        self.last_right_eye_drawn_bbox: Optional[Tuple[int, int, int, int]] = None
        self.last_mouth_drawn_bbox: Optional[Tuple[int, int, int, int]] = None
        self.last_text_drawn_bbox: Optional[Tuple[int, int, int, int]] = None

    def _get_eye_bbox(self, center_x: int, center_y: int, radius: int) -> Tuple[int, int, int, int]:
        return (
            center_x - radius,
            center_y - radius,
            center_x + radius,
            center_y + radius,
        )

    def _draw_overlay_text(self, image_buffer: Image.Image, text: str, y_offset_ratio: float = 0.0) -> Tuple[int, int, int, int]:
        """Draws overlay text and returns its bounding box."""
        draw = ImageDraw.Draw(image_buffer)
        
        # Calculate clear region: previous text bbox + current text potential bbox
        clear_region = self.last_text_drawn_bbox
        
        # Temporarily draw text to get its bbox without affecting the main image
        temp_img = Image.new('RGBA', (self.width, self.height), (0, 0, 0, 0))
        temp_draw = ImageDraw.Draw(temp_img)
        temp_draw.text((0, int(self.height * y_offset_ratio)), text, font=self.font, fill=TEXT_COLOR)
        current_text_bbox_raw = temp_img.getbbox()

        if current_text_bbox_raw:
            # Adjust bbox to actual position on screen
            current_text_bbox = (
                current_text_bbox_raw[0],
                int(self.height * y_offset_ratio) + current_text_bbox_raw[1],
                current_text_bbox_raw[2],
                int(self.height * y_offset_ratio) + current_text_bbox_raw[3]
            )
            clear_region = merge_bboxes(clear_region, current_text_bbox)
        else:
            current_text_bbox = None

        # Clear previous text area if any
        if clear_region:
            draw.rectangle(clear_region, fill=BACKGROUND_COLOR)

        # Draw new text
        if current_text_bbox:
            draw_text(
                draw,
                text,
                self.font,
                x="center",
                y=int(self.height * y_offset_ratio),
                width=self.width,
                height=self.height,
                color=TEXT_COLOR,
            )
        
        self.last_text_drawn_bbox = current_text_bbox
        return clear_region # Return the merged clear/drawn region as dirty

    def _clear_overlay_text(self, image_buffer: Image.Image) -> Optional[Tuple[int, int, int, int]]:
        """Clears the previously drawn overlay text."""
        if self.last_text_drawn_bbox:
            draw = ImageDraw.Draw(image_buffer)
            draw.rectangle(self.last_text_drawn_bbox, fill=BACKGROUND_COLOR)
            cleared_bbox = self.last_text_drawn_bbox
            self.last_text_drawn_bbox = None
            return cleared_bbox
        return None

    def draw_eyes(self, image_buffer: Image.Image, state: str = "open", color: Tuple[int, int, int] = (255, 255, 255)) -> Tuple[int, int, int, int]:
        """Draws the robot's eyes based on the given state."""
        draw = ImageDraw.Draw(image_buffer)
        
        # Calculate clear region: previous drawn bboxes + current base bboxes
        clear_region = merge_bboxes(self.last_left_eye_drawn_bbox, self.last_right_eye_drawn_bbox)
        clear_region = merge_bboxes(clear_region, self.left_eye_base_bbox)
        clear_region = merge_bboxes(clear_region, self.right_eye_base_bbox)

        # Clear the entire base area for both eyes to ensure no residue
        draw.rectangle(self.left_eye_base_bbox, fill=BACKGROUND_COLOR)
        draw.rectangle(self.right_eye_base_bbox, fill=BACKGROUND_COLOR)
        base_clear_region = merge_bboxes(self.left_eye_base_bbox, self.right_eye_base_bbox)

        drawn_bboxes = []

        if state == "open":
            # Draw outer circle (white)
            draw.ellipse(self.left_eye_base_bbox, fill=color, outline=color)
            draw.ellipse(self.right_eye_base_bbox, fill=color, outline=color)
            drawn_bboxes.append(self.left_eye_base_bbox)
            drawn_bboxes.append(self.right_eye_base_bbox)

            # Draw inner circle (black) to create a hollow effect
            inner_radius = int(self.eye_radius * 0.6)
            left_inner_bbox = self._get_eye_bbox(self.left_eye_center_x, self.eye_y, inner_radius)
            right_inner_bbox = self._get_eye_bbox(self.right_eye_center_x, self.eye_y, inner_radius)
            draw.ellipse(left_inner_bbox, fill=BACKGROUND_COLOR)
            draw.ellipse(right_inner_bbox, fill=BACKGROUND_COLOR)
            drawn_bboxes.append(left_inner_bbox)
            drawn_bboxes.append(right_inner_bbox)

        elif state == "closed":
            # Draw an upward arc for closed eyes, covering the full eye radius vertically
            arc_height = self.eye_radius # Ensure it covers the full vertical extent of the eye
            
            # Left eye arc
            left_arc_bbox = (
                self.left_eye_base_bbox[0],
                self.eye_y - arc_height, # Start arc higher
                self.left_eye_base_bbox[2],
                self.eye_y + arc_height  # End arc lower
            )
            draw.arc(left_arc_bbox, start=180, end=360, fill=color, width=2)
            drawn_bboxes.append(left_arc_bbox)

            # Right eye arc
            right_arc_bbox = (
                self.right_eye_base_bbox[0],
                self.eye_y - arc_height, # Start arc higher
                self.right_eye_base_bbox[2],
                self.eye_y + arc_height  # End arc lower
            )
            draw.arc(right_arc_bbox, start=180, end=360, fill=color, width=2)
            drawn_bboxes.append(right_arc_bbox)

        elif state == "happy_eyes":
            # Filled eyes for happy expression
            draw.ellipse(self.left_eye_base_bbox, fill=color, outline=color)
            draw.ellipse(self.right_eye_base_bbox, fill=color, outline=color)
            drawn_bboxes.append(self.left_eye_base_bbox)
            drawn_bboxes.append(self.right_eye_base_bbox)

        elif state == "sad_eyes":
            # Eyes looking up/inward (by shifting inner black circle)
            inner_radius = int(self.eye_radius * 0.6)
            pupil_offset_x = int(self.eye_radius * 0.2)
            pupil_offset_y = int(self.eye_radius * 0.2)
            
            draw.ellipse(self.left_eye_base_bbox, fill=color, outline=color)
            draw.ellipse(self.right_eye_base_bbox, fill=color, outline=color)
            drawn_bboxes.append(self.left_eye_base_bbox)
            drawn_bboxes.append(self.right_eye_base_bbox)
            
            left_pupil_bbox = self._get_eye_bbox(self.left_eye_center_x - pupil_offset_x, self.eye_y - pupil_offset_y, inner_radius)
            right_pupil_bbox = self._get_eye_bbox(self.right_eye_center_x + pupil_offset_x, self.eye_y - pupil_offset_y, inner_radius)
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
            
            left_pupil_bbox = self._get_eye_bbox(self.left_eye_center_x + pupil_offset_x, self.eye_y - pupil_offset_y, inner_radius)
            right_pupil_bbox = self._get_eye_bbox(self.right_eye_center_x - pupil_offset_x, self.eye_y - pupil_offset_y, inner_radius)
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

        return merge_bboxes(base_clear_region, drawn_region) # Return the merged clear/drawn region as dirty