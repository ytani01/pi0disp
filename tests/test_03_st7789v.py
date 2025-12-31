"""Tests for ST7789V driver."""

from unittest.mock import patch

import pytest

from pi0disp.disp.st7789v import ST7789V


@pytest.fixture
def mock_pigpio():
    with patch("pigpio.pi") as mock_pi:
        mock_instance = mock_pi.return_value
        mock_instance.connected = True
        mock_instance.spi_open.return_value = 1
        yield mock_instance


def test_init_success(mock_pigpio):
    """ST7789Vの初期化成功をテスト."""
    disp = ST7789V()
    assert disp.spi_handle == 1
    assert mock_pigpio.spi_open.called
    disp.close()


def test_color_settings(mock_pigpio):
    """invert と bgr の設定が反映されるかテスト."""
    disp = ST7789V(invert=False, bgr=True)
    assert disp._invert is False
    assert disp._bgr is True
    disp.close()


def test_madctl_bgr_bit(mock_pigpio):
    """bgr=True の時に MADCTL の BGR ビットが立つか確認."""
    # Reset mock after init
    with patch(
        "pi0disp.disp.st7789v.ST7789V.init_display"
    ):  # Skip init_display for simplicity
        disp = ST7789V(bgr=True)
        # Clear previous calls
        mock_pigpio.spi_write.reset_mock()
        disp.set_rotation(0)
        # MADCTL (0x36) followed by data 0x08
        mock_pigpio.spi_write.assert_any_call(1, [0x08])
        disp.close()


def test_invon_off_commands(mock_pigpio):
    """invert 設定によって INVON/INVOFF コマンドが飛ぶか確認."""
    # invert=True
    mock_pigpio.spi_write.reset_mock()
    disp1 = ST7789V(invert=True)
    mock_pigpio.spi_write.assert_any_call(1, [0x21])  # INVON
    disp1.close()

    # invert=False
    mock_pigpio.spi_write.reset_mock()
    disp2 = ST7789V(invert=False)
    mock_pigpio.spi_write.assert_any_call(1, [0x20])  # INVOFF
    disp2.close()


def test_set_rotation(mock_pigpio):
    """set_rotation でサイズと MADCTL が正しく更新されるか."""
    disp = ST7789V()

    # 90度 (EAST)
    mock_pigpio.spi_write.reset_mock()
    disp.set_rotation(90)
    assert disp.size.width == 320
    assert disp.size.height == 240
    # MADCTL 0x60 (EAST)
    mock_pigpio.spi_write.assert_any_call(1, [0x60])

    # 180度 (SOUTH)
    mock_pigpio.spi_write.reset_mock()
    disp.set_rotation(180)
    assert disp.size.width == 240
    assert disp.size.height == 320
    # MADCTL 0xC0 (SOUTH)
    mock_pigpio.spi_write.assert_any_call(1, [0xC0])

    disp.close()


def test_close(mock_pigpio):
    """close 時にスリープコマンドが飛ぶか確認."""
    disp = ST7789V()
    mock_pigpio.spi_write.reset_mock()
    disp.close()
    mock_pigpio.spi_write.assert_any_call(1, [0x28])  # DISPOFF
    mock_pigpio.spi_write.assert_any_call(1, [0x10])  # SLPIN
    assert mock_pigpio.spi_close.called
