"""Tests for ST7789V display driver."""
from unittest.mock import MagicMock, patch, call
import pytest
from PIL import Image
from pi0disp import ST7789V, DispSize, SpiPins

def create_st7789v_instance():
    return ST7789V(pin=SpiPins(rst=25, dc=24, bl=23), size=DispSize(240, 320), rotation=0)

def test_init_success(mock_pi_instance):
    disp = create_st7789v_instance()
    assert disp.pi == mock_pi_instance

def test_set_rotation(mock_pi_instance):
    disp = create_st7789v_instance()
    disp.set_rotation(ST7789V.EAST)
    assert disp.rotation == 90
    assert disp.size == DispSize(320, 240)

def test_close(mock_pi_instance):
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()
    disp.close()
    # DISPOFF(0x28), SLPIN(0x10) が呼ばれることを確認
    calls = [c[0][1] for c in mock_pi_instance.spi_write.call_args_list]
    assert [0x28] in calls
    assert [0x10] in calls
