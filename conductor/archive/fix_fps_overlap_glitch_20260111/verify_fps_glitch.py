# -*- coding: utf-8 -*-
import os
import sys
from unittest.mock import MagicMock, patch

from PIL import Image, ImageFont

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "src"))
)

from pi0disp.commands.ballanime import _loop


def verify_mode(mode: str):
    print(f"--- Verifying mode: {mode} ---")
    lcd = MagicMock()
    lcd.size.width = 320
    lcd.size.height = 240
    bg = Image.new("RGB", (320, 240), (0, 0, 0))

    ball1 = MagicMock()
    ball1.get_dirty_region.return_value = (120, 20, 40, 40)
    ball1.fill_color = (255, 0, 0)
    ball1.cx = 140
    ball1.cy = 40
    ball1.radius = 20
    ball1.bbox = (120, 20, 160, 60)

    ball2 = MagicMock()
    ball2.get_dirty_region.return_value = (0, 60, 40, 40)
    ball2.fill_color = (0, 255, 0)
    ball2.cx = 20
    ball2.cy = 80
    ball2.radius = 20
    ball2.bbox = (0, 60, 40, 100)

    balls = [ball1, ball2]

    fps_counter = MagicMock()
    fps_counter.fps_text = "FPS: 99"
    fps_counter.update.side_effect = [True, False, False, False]

    tracker = MagicMock()
    tracker.should_stop.side_effect = [False, False, True]

    font = ImageFont.load_default()

    captured_images = []

    def mock_display_region(img, x0, y0, x1, y1):
        captured_images.append(img.copy())

    lcd.display_region.side_effect = mock_display_region

    with (
        patch("time.sleep"),
        patch("pi0disp.commands.ballanime._handle_ball_collisions_optimized"),
        patch(
            "pi0disp.commands.ballanime.RegionOptimizer.merge_regions"
        ) as mock_merge,
    ):
        # Frame 1: Return original regions (Separated from FPS)
        # Frame 2: Return a merged region that covers FPS area (0,0,100,40)
        # Frame 3: Same
        mock_merge.side_effect = [
            [(120, 20, 40, 40), (0, 60, 40, 40)],  # Frame 1
            [(0, 0, 160, 100)],  # Frame 2 (Wipes FPS area)
            [(0, 0, 160, 100)],  # Frame 3
        ]

        _loop(
            lcd,
            bg,
            balls,  # type: ignore[arg-type]
            fps_counter,
            font,
            30.0,
            mode=mode,
            tracker=tracker,
        )

    if not captured_images:
        print(f"FAILED: No display update for {mode}")
        return False

    # Frame 2 image
    final_img = captured_images[-1]
    pixels = final_img.crop((0, 0, 100, 40)).getdata()
    has_text = any(sum(p) > 0 for p in pixels)

    if not has_text:
        print(f"FAILED: FPS Text missing in {mode} area!")
        final_img.save(f"glitch_fail_{mode}.png")
        return False

    print(f"PASSED: {mode}")
    return True


if __name__ == "__main__":
    success = True
    if not verify_mode("optimized"):
        success = False
    if not verify_mode("cairo-optimized"):
        success = False
    if not success:
        sys.exit(1)
    sys.exit(0)
