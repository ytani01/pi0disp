"""Tests for DispSpi class."""

from unittest.mock import patch

import pytest

from pi0disp.disp.disp_spi import DispSpi, SpiPins


@pytest.fixture
def mock_pigpio():
    with patch("pigpio.pi") as mock_pi:
        mock_instance = mock_pi.return_value
        mock_instance.connected = True
        mock_instance.spi_open.return_value = 1
        yield mock_instance


def test_init_success(mock_pigpio):
    disp = DispSpi()
    assert disp.spi_handle == 1
    assert mock_pigpio.spi_open.called
    disp.close()


def test_init_spi_open_error(mock_pigpio):
    mock_pigpio.spi_open.return_value = -1
    with pytest.raises(RuntimeError, match="SPIバスを開けませんでした"):
        DispSpi()


def test_init_custom_pin(mock_pigpio):
    custom_pins = SpiPins(rst=1, dc=2, cs=3, bl=4)
    disp = DispSpi(pin=custom_pins)
    assert disp.pin.rst == 1
    assert disp.pin.bl == 4
    # Check if set_mode was called for each pin
    mock_pigpio.set_mode.assert_any_call(1, 1)  # 1 is OUTPUT
    mock_pigpio.set_mode.assert_any_call(4, 1)
    disp.close()


def test_init_no_bl_pin(mock_pigpio):
    pins = SpiPins(rst=1, dc=2, cs=3, bl=None)
    disp = DispSpi(pin=pins)
    assert disp.pin.bl is None
    disp.set_backlight(True)
    # PWM should NOT be called if bl is None
    assert not mock_pigpio.set_PWM_dutycycle.called
    disp.close()


def test_enter_exit_context_manager(mock_pigpio):
    with DispSpi() as disp:
        assert disp.spi_handle == 1
    assert mock_pigpio.spi_close.called


def test_write_command(mock_pigpio):
    disp = DispSpi()
    disp._write_command(0xAF)
    mock_pigpio.write.assert_any_call(disp.pin.dc, 0)
    mock_pigpio.spi_write.assert_called_with(disp.spi_handle, [0xAF])
    disp.close()


def test_write_data_int(mock_pigpio):
    disp = DispSpi()
    disp._write_data(0x55)
    mock_pigpio.write.assert_any_call(disp.pin.dc, 1)
    mock_pigpio.spi_write.assert_called_with(disp.spi_handle, [0x55])
    disp.close()


def test_write_data_bytes_list(mock_pigpio):
    disp = DispSpi()
    data = [0x01, 0x02, 0x03]
    disp._write_data(data)
    mock_pigpio.spi_write.assert_called_with(disp.spi_handle, data)
    disp.close()


def test_set_backlight(mock_pigpio):
    disp = DispSpi()
    disp.set_backlight(True)
    mock_pigpio.set_PWM_dutycycle.assert_called_with(disp.pin.bl, 255)
    disp.set_backlight(False)
    mock_pigpio.set_PWM_dutycycle.assert_called_with(disp.pin.bl, 0)
    disp.close()


def test_set_brightness(mock_pigpio):
    disp = DispSpi()
    disp.set_backlight(True)
    disp.set_brightness(128)
    mock_pigpio.set_PWM_dutycycle.assert_called_with(disp.pin.bl, 128)
    disp.close()


def test_set_brightness_bl_off(mock_pigpio):
    disp = DispSpi()
    disp.set_backlight(False)
    disp.set_brightness(128)
    # PWM should not be called if backlight is OFF
    mock_pigpio.set_PWM_dutycycle.assert_any_call(disp.pin.bl, 0)
    # Should NOT have been called with 128 yet
    for call in mock_pigpio.set_PWM_dutycycle.call_args_list:
        assert call[0][1] != 128
    disp.close()


def test_close_spi_close_error(mock_pigpio):
    # Setup: mock only fails when specifically requested during close()
    should_fail = False

    def side_effect(handle):
        if should_fail and handle == 1:
            raise Exception("SPI close error")
        return None

    mock_pigpio.spi_close.side_effect = side_effect

    disp = DispSpi()
    should_fail = True  # Enable failure for the close() call
    disp.close()  # Should not raise exception because we catch it in close()
    assert mock_pigpio.spi_close.called


def test_close_not_connected(mock_pigpio):
    disp = DispSpi()
    # Reset call count because __init__ calls spi_close 32 times
    mock_pigpio.spi_close.reset_mock()

    mock_pigpio.connected = False
    disp.close()
    # spi_close should NOT be called in close() if not connected
    assert not mock_pigpio.spi_close.called


def test_close_with_bl_off(mock_pigpio):
    disp = DispSpi()
    disp.set_backlight(True)
    disp.close()
    mock_pigpio.set_PWM_dutycycle.assert_any_call(disp.pin.bl, 0)


def test_close_no_backlight_pin(mock_pigpio):
    pins = SpiPins(rst=1, dc=2, cs=3, bl=None)
    disp = DispSpi(pin=pins)
    disp.close()
    assert not mock_pigpio.set_PWM_dutycycle.called
