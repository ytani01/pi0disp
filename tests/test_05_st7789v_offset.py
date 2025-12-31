"""Tests for ST7789V offset functionality."""
from unittest.mock import MagicMock, patch
import pytest
from pi0disp import ST7789V, DispSize, SpiPins

def test_set_window_with_offset(mock_pi_instance):
    x_off, y_off = 10, 20
    disp = ST7789V(pin=SpiPins(rst=25, dc=24, bl=23), size=DispSize(240, 320), x_offset=x_off, y_offset=y_off, rotation=0)
    mock_pi_instance.reset_mock()
    disp.set_window(0, 0, 100, 100)
    calls = mock_pi_instance.spi_write.call_args_list
    caset, raset = False, False
    for i in range(len(calls) - 1):
        p, c = calls[i][0][1], calls[i+1][0][1]
        if p == [0x2A] and c == [0, 10, 0, 110]: caset = True
        if p == [0x2B] and c == [0, 20, 0, 120]: raset = True
    assert caset and raset

def test_set_window_rotation_90(mock_pi_instance):
    disp = ST7789V(pin=SpiPins(rst=25, dc=24, bl=23), size=DispSize(240, 320), rotation=90, x_offset=10, y_offset=20)
    mock_pi_instance.reset_mock()
    disp.set_window(0, 0, 319, 239)
    calls = mock_pi_instance.spi_write.call_args_list
    c_x, r_y = False, False
    for i in range(len(calls) - 1):
        p, c = calls[i][0][1], calls[i+1][0][1]
        if p == [0x2A] and c == [0, 20, 1, 83]: c_x = True
        if p == [0x2B] and c == [0, 10, 0, 249]: r_y = True
    assert c_x and r_y
