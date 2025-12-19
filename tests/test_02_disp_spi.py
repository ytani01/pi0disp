"""Tests for DispSpi."""

from unittest.mock import ANY, call, patch

import pigpio
import pytest

from pi0disp.disp.disp_base import DispBase, DispSize
from pi0disp.disp.disp_spi import DispSpi, SpiPins

# Constants
CMD_TEST = 0x10
DATA_TEST_INT = 0x20
DATA_TEST_BYTES = [0x01, 0x02, 0x03]
DEFAULT_SIZE = DispSize(240, 320)
DEFAULT_PIN = SpiPins(rst=25, dc=24, bl=23)
DEFAULT_CHANNEL = 0
DEFAULT_SPEED_HZ = 60_000_000
DEFAULT_ROTATION = DispBase.DEF_ROTATION


@pytest.fixture
def mock_sleep():
    """Mock time.sleep."""
    with patch("time.sleep") as mock:
        yield mock


@pytest.fixture
def mock_disp_base_init(mock_pi_instance, mock_logger):
    """Mock DispBase.__init__."""

    def _simple_disp_base_init_side_effect(
        obj_self, size, rotation, debug=False
    ):
        obj_self.pi = mock_pi_instance
        obj_self.pi.connected = True
        obj_self._native_size = size
        obj_self.size = size
        obj_self._rotation = rotation
        obj_self.debug = debug
        obj_self.__log = mock_logger

    with patch(
        "pi0disp.disp.disp_base.DispBase.__init__", autospec=True
    ) as mock_init:
        mock_init.return_value = None
        mock_init.side_effect = _simple_disp_base_init_side_effect
        yield mock_init


def create_disp_spi_instance(
    size: DispSize | None = None,
    rotation: int = DEFAULT_ROTATION,
    bl_at_close: bool = False,
    channel: int = DEFAULT_CHANNEL,
    pin: SpiPins | None = None,
    speed_hz: int = DEFAULT_SPEED_HZ,
    brightness: int = 255,
    debug: bool = False,
) -> DispSpi:
    """Helper to create DispSpi instance."""
    if size is None:
        size = DEFAULT_SIZE
    if pin is None:
        pin = DEFAULT_PIN

    return DispSpi(
        size=size,
        rotation=rotation,
        bl_at_close=bl_at_close,
        channel=channel,
        pin=pin,
        speed_hz=speed_hz,
        brightness=brightness,
        debug=debug,
    )


def test_init_success(
    mock_disp_base_init, mock_pi_instance, mock_sleep, mock_logger
):
    """初期化成功時のテスト."""
    size = DispSize(240, 240)
    disp = create_disp_spi_instance(size=size)

    mock_disp_base_init.assert_called_once_with(
        disp, size, DEFAULT_ROTATION, debug=False
    )
    mock_pi_instance.set_mode.assert_any_call(DEFAULT_PIN.dc, pigpio.OUTPUT)
    mock_pi_instance.set_mode.assert_any_call(DEFAULT_PIN.rst, pigpio.OUTPUT)
    mock_pi_instance.set_mode.assert_any_call(DEFAULT_PIN.bl, pigpio.OUTPUT)
    mock_pi_instance.spi_open.assert_called_once_with(
        DEFAULT_CHANNEL, DEFAULT_SPEED_HZ, 0
    )

    assert not disp.bl_at_close
    assert disp.spi_handle == 0


def test_init_spi_open_error(mock_pi_instance, mock_disp_base_init):
    """spi_open()失敗時のテスト."""
    mock_pi_instance.spi_open.return_value = -1
    size = DispSize(240, 320)

    with pytest.raises(RuntimeError):
        create_disp_spi_instance(size=size)

    mock_disp_base_init.assert_called_once_with(
        ANY, size, DEFAULT_ROTATION, debug=False
    )


def test_init_custom_pin(mock_pi_instance, mock_disp_base_init):
    """ピン配置指定時のテスト."""
    custom_pin = SpiPins(rst=11, dc=10, bl=12)
    size = DispSize(240, 320)
    disp = create_disp_spi_instance(pin=custom_pin, size=size)

    mock_disp_base_init.assert_called_once_with(
        disp, size, DEFAULT_ROTATION, debug=False
    )
    mock_pi_instance.set_mode.assert_any_call(custom_pin.dc, pigpio.OUTPUT)
    mock_pi_instance.set_mode.assert_any_call(custom_pin.rst, pigpio.OUTPUT)
    mock_pi_instance.set_mode.assert_any_call(custom_pin.bl, pigpio.OUTPUT)
    assert disp.pin == custom_pin


def test_init_no_bl_pin(mock_pi_instance, mock_disp_base_init):
    """バックライトピンなし構成のテスト."""
    no_bl_pin = SpiPins(rst=11, dc=10, bl=None)
    create_disp_spi_instance(pin=no_bl_pin)

    # BLピンへのset_modeがないことを確認
    # (全ての引数を取得して期待していないピン番号が含まれていないかチェック)
    for call_args in mock_pi_instance.set_mode.call_args_list:
        assert call_args[0][0] is not None

    # BLピンへのwriteがないことを確認
    # (初期化シーケンスでrst=1, rst=0, rst=1 のあとに bl=ON が呼ばれない)
    # 実際には reset_mock してから呼ぶのが綺麗だが、ここでは呼び出しを確認しないことで担保
    for call_args in mock_pi_instance.set_PWM_dutycycle.call_args_list:
        assert call_args[0][0] is not None


def test_enter_exit_context_manager(mock_pi_instance, mock_disp_base_init):
    """コンテキストマネージャ (__enter__, __exit__) のテスト."""
    with patch.object(DispBase, "close") as mock_super_close:
        mock_super_close.side_effect = (
            lambda *args: mock_pi_instance.stop()
            if mock_pi_instance.connected
            else None
        )
        with create_disp_spi_instance() as disp:
            assert isinstance(disp, DispSpi)

        mock_super_close.assert_called_once()


def test_write_command(mock_pi_instance, mock_disp_base_init):
    """_write_command()のテスト."""
    disp = create_disp_spi_instance()
    disp._write_command(CMD_TEST)

    mock_pi_instance.write.assert_any_call(disp.pin.dc, 0)
    mock_pi_instance.spi_write.assert_called_once_with(
        disp.spi_handle, [CMD_TEST]
    )


def test_write_data_int(mock_pi_instance, mock_disp_base_init):
    """_write_data(int)のテスト."""
    disp = create_disp_spi_instance()
    disp._write_data(DATA_TEST_INT)

    mock_pi_instance.write.assert_any_call(disp.pin.dc, 1)
    mock_pi_instance.spi_write.assert_called_once_with(
        disp.spi_handle, [DATA_TEST_INT]
    )


def test_write_data_bytes_list(mock_pi_instance, mock_disp_base_init):
    """_write_data(list)のテスト."""
    disp = create_disp_spi_instance()
    disp._write_data(DATA_TEST_BYTES)

    mock_pi_instance.write.assert_any_call(disp.pin.dc, 1)
    mock_pi_instance.spi_write.assert_called_once_with(
        disp.spi_handle, DATA_TEST_BYTES
    )


def test_set_brightness(mock_pi_instance, mock_disp_base_init):
    """set_brightness()のテスト."""
    disp = create_disp_spi_instance()
    disp.set_backlight(True)
    mock_pi_instance.set_PWM_dutycycle.reset_mock()

    disp.set_brightness(128)
    assert disp._brightness == 128
    mock_pi_instance.set_PWM_dutycycle.assert_called_with(disp.pin.bl, 128)


def test_set_backlight(mock_pi_instance, mock_disp_base_init):
    """set_backlight()のテスト."""
    disp = create_disp_spi_instance(brightness=200)

    # ON
    disp.set_backlight(True)
    assert disp._backlight_on is True
    mock_pi_instance.set_PWM_dutycycle.assert_called_with(disp.pin.bl, 200)

    # OFF
    disp.set_backlight(False)
    assert disp._backlight_on is False
    mock_pi_instance.set_PWM_dutycycle.assert_called_with(disp.pin.bl, 0)


def test_init_display(mock_pi_instance, mock_sleep, mock_disp_base_init):
    """init_display()のテスト."""
    disp = create_disp_spi_instance()
    disp.init_display()

    # RSTピンの制御
    mock_pi_instance.write.assert_any_call(disp.pin.rst, 1)
    mock_pi_instance.write.assert_any_call(disp.pin.rst, 0)
    mock_pi_instance.write.assert_any_call(disp.pin.rst, 1)
    mock_sleep.assert_has_calls([call(0.01), call(0.01), call(0.150)])

    # バックライトの制御
    mock_pi_instance.set_PWM_dutycycle.assert_any_call(disp.pin.bl, 255)


def test_close_with_bl_off(mock_pi_instance, mock_disp_base_init):
    """close()のテスト (bl_at_close=False)."""
    with patch.object(DispBase, "close") as mock_super_close:
        mock_super_close.side_effect = (
            lambda *args: mock_pi_instance.stop()
            if mock_pi_instance.connected
            else None
        )
        # bl_at_close=False (default) の場合
        disp = create_disp_spi_instance()
        disp.pi.connected = True
        disp.close()

        mock_pi_instance.stop.assert_called_once()
        mock_super_close.assert_called_once()
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(disp.pin.bl, 0)


def test_close_with_bl_on(mock_pi_instance, mock_disp_base_init):
    """close()のテスト (bl_at_close=True)."""
    with patch.object(DispBase, "close") as mock_super_close:
        mock_super_close.side_effect = (
            lambda *args: mock_pi_instance.stop()
            if mock_pi_instance.connected
            else None
        )
        # bl_at_close=True の場合
        disp = create_disp_spi_instance(bl_at_close=True)
        disp.pi.connected = True
        disp.close()

        # ここでは呼び出し自体を確認
        mock_pi_instance.stop.assert_called_once()
        mock_super_close.assert_called_once()
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(disp.pin.bl, 255)
