#
# (c) 2026 Yoichi Tanibayashi
#
"""Tests for orientation test pattern drawing."""

from pi0disp.utils.lcd_test_pattern import draw_orientation_pattern
from PIL import Image

def test_draw_orientation_pattern_scaling():
    """Verify scaling and content of orientation pattern."""
    
    # 1. Portrait (240x320)
    w, h = 240, 320
    img = draw_orientation_pattern(w, h, 0)
    assert isinstance(img, Image.Image)
    assert img.size == (w, h)
    
    # 保存して目視確認用（デバッグ用）
    img.save("test_orientation_portrait.png")

    # 2. Landscape (320x240)
    w, h = 320, 240
    img = draw_orientation_pattern(w, h, 90)
    assert isinstance(img, Image.Image)
    assert img.size == (w, h)
    
    img.save("test_orientation_landscape.png")

def test_draw_orientation_pattern_rotations():
    """Verify all 4 rotations are accepted."""
    for rot in [0, 90, 180, 270]:
        img = draw_orientation_pattern(240, 240, rot)
        assert img.size == (240, 240)
