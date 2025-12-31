"""Tests for ST7789V offset functionality."""

from unittest.mock import MagicMock, patch
import pytest
from pi0disp import ST7789V, DispSize, SpiPins

def test_set_window_with_offset(mock_pi_instance):
    """Test that set_window applies x_offset and y_offset correctly."""
    # Initialize with offsets
    x_off = 10
    y_off = 20
    disp = ST7789V(
        pin=SpiPins(rst=25, dc=24, bl=23),
        size=DispSize(240, 320),
        x_offset=x_off,
        y_offset=y_off
    )
    
    mock_pi_instance.reset_mock()
    
    # Request a window from (0, 0) to (100, 100)
    # Note: If default rotation is 270 (MV=1), CASET and RASET will be swapped.
    # We check MV state to know expectation.
    disp.set_window(0, 0, 100, 100)
    
    calls = mock_pi_instance.spi_write.call_args_list
    caset_data_found = False
    raset_data_found = False
    
    expected_caset = [0, 10, 0, 110] if not disp._mv else [0, 20, 0, 120]
    expected_raset = [0, 20, 0, 120] if not disp._mv else [0, 10, 0, 110]

    for i in range(len(calls) - 1):
        prev_data = calls[i][0][1]
        curr_data = calls[i+1][0][1]
        
        if prev_data == [0x2A]: # CASET
            if curr_data == expected_caset:
                caset_data_found = True
            
        if prev_data == [0x2B]: # RASET
            if curr_data == expected_raset:
                raset_data_found = True
            
    assert caset_data_found, f"CASET data {expected_caset} was not written. MV={disp._mv}, Calls: {calls}"
    assert raset_data_found, f"RASET data {expected_raset} was not written. MV={disp._mv}, Calls: {calls}"

def test_set_window_rotation_90(mock_pi_instance):
    """Test that set_window swaps CASET/RASET when rotation is 90 (MV=1)."""
    disp = ST7789V(
        pin=SpiPins(rst=25, dc=24, bl=23),
        size=DispSize(240, 320),
        rotation=90 # MV=1
    )
    
    mock_pi_instance.reset_mock()
    
    # Logical window (0, 0) to (319, 239)
    # Since MV=1:
    # CASET should get Y (0, 239)
    # RASET should get X (0, 319)
    disp.set_window(0, 0, 319, 239)
    
    calls = mock_pi_instance.spi_write.call_args_list
    caset_y_found = False
    raset_x_found = False
    
    for i in range(len(calls) - 1):
        prev_data = calls[i][0][1]
        curr_data = calls[i+1][0][1]
        if prev_data == [0x2A]: # CASET
            if curr_data == [0, 0, 0, 239]:
                caset_y_found = True
        if prev_data == [0x2B]: # RASET
            if curr_data == [0, 0, 1, 63]: # 319 = 0x013F
                raset_x_found = True
            
    assert caset_y_found, f"CASET should receive Y coordinates when MV=1. Calls: {calls}"
    assert raset_x_found, f"RASET should receive X coordinates when MV=1. Calls: {calls}"

