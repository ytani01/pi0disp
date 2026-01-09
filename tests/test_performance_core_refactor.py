# -*- coding: utf-8 -*-
import numpy as np
import pytest
from pi0disp.utils.performance_core import ColorConverter
from pi0disp.utils.utils import merge_bboxes, clamp_region, pil_to_rgb565_bytes
from PIL import Image
import subprocess
import sys
import re


def test_color_converter_basic():
    """RGB to RGB565 basic conversion check."""
    cc = ColorConverter()
    
    # Red (255, 0, 0) -> RGB565 (11111 000000 00000) = 0xF800 (Big Endian)
    rgb = np.array([[[255, 0, 0]]], dtype=np.uint8)
    expected = b'\xf8\x00'
    assert cc.convert(rgb) == expected

    # Green (0, 255, 0) -> RGB565 (00000 111111 00000) = 0x07E0
    rgb = np.array([[[0, 255, 0]]], dtype=np.uint8)
    expected = b'\x07\xe0'
    assert cc.convert(rgb) == expected

    # Blue (0, 0, 255) -> RGB565 (00000 000000 11111) = 0x001F
    rgb = np.array([[[0, 0, 255]]], dtype=np.uint8)
    expected = b'\x00\x1f'
    assert cc.convert(rgb) == expected

def test_color_converter_gamma():
    """Gamma correction check."""
    cc = ColorConverter(gamma=1.0) # Linear
    rgb = np.array([[[128, 128, 128]]], dtype=np.uint8)
    out1 = cc.convert(rgb, apply_gamma=True)
    
    cc.set_gamma(2.0)
    out2 = cc.convert(rgb, apply_gamma=True)
    
    # With gamma=2.0, brightness 128 should become around 255 * (128/255)^2 = 64
    assert out1 != out2

def test_utils_merge_bboxes():
    """Bounding box merging logic."""
    assert merge_bboxes(None, (10, 10, 20, 20)) == (10, 10, 20, 20)
    assert merge_bboxes((0, 0, 5, 5), (10, 10, 15, 15)) == (0, 0, 15, 15)
    assert merge_bboxes((5, 5, 15, 15), (10, 10, 20, 20)) == (5, 5, 20, 20)

def test_utils_clamp_region():
    """Region clamping logic."""
    assert clamp_region((-10, -10, 300, 300), 240, 320) == (0, 0, 240, 300)
    assert clamp_region((10, 10, 50, 50), 240, 320) == (10, 10, 50, 50)

def test_pil_to_rgb565_bytes():
    """Integration check for PIL image conversion."""
    img = Image.new("RGB", (2, 2), (255, 0, 0)) # 2x2 red square
    data = pil_to_rgb565_bytes(img)
    # 4 pixels * 2 bytes = 8 bytes. All pixels should be 0xF800
    assert len(data) == 8
    assert data == b'\xf8\x00\xf8\x00\xf8\x00\xf8\x00'

def run_script_and_capture(script_path: str) -> str:
    """指定されたPythonスクリプトを実行し、標準出力を返す"""
    result = subprocess.run(
        [sys.executable, script_path],
        capture_output=True,
        text=True,
        check=True
    )
    return result.stdout

def test_sample_color_converter():
    """Test the color converter sample script."""
    script_path = "conductor/tracks/performance_core_refactor_20260109/sample_color_converter.py"
    output = run_script_and_capture(script_path)
    
    assert "--- ColorConverter Sample ---" in output
    # Check for hex output format
    assert re.search(r"RGB565 bytes \(no gamma, first 16 bytes\): [0-9a-f]+", output)
    assert re.search(r"RGB565 bytes \(with gamma 1.0, first 16 bytes\): [0-9a-f]+", output)

def test_sample_region_utils():
    """Test the region utils sample script."""
    script_path = "conductor/tracks/performance_core_refactor_20260109/sample_region_utils.py"
    output = run_script_and_capture(script_path)

    assert "--- Region Utilities Sample ---" in output
    assert "Merged (BBox1, BBox2): (x0=10, y0=10, x1=70, y1=70)" in output
    assert "Clamped Overlap: (x0=0, y0=0, x1=100, y1=100)" in output

