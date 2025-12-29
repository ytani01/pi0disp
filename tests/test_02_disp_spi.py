"""Tests for DispSpi."""

from unittest.mock import ANY, MagicMock, PropertyMock, call, patch

import pigpio
import pytest

from pi0disp import DispBase, DispSize, DispSpi, SpiPins

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
        obj_self._size = size
        obj_self._rotation = rotation
        obj_self.debug = debug
        obj_self._log = mock_logger  # Changed: set _log and uncommented

    with patch(
        "pi0disp.disp.disp_base.DispBase.__init__", autospec=True
    ) as mock_init:
        mock_init.return_value = None
        mock_init.side_effect = _simple_disp_base_init_side_effect
        yield mock_init


def create_disp_spi_instance(
    bl_at_close: bool = False,
    pin: SpiPins | None = None,
    brightness: int = 255,
    channel: int = DEFAULT_CHANNEL,
    speed_hz: int = DEFAULT_SPEED_HZ,
    size: DispSize | None = None,
    rotation: int = DEFAULT_ROTATION,
    debug: bool = False,
) -> DispSpi:
    """Helper to create DispSpi instance."""
    if size is None:
        size = DEFAULT_SIZE
    if pin is None:
        pin = DEFAULT_PIN

    display = DispSpi(
        bl_at_close=bl_at_close,
        pin=pin,
        brightness=brightness,
        channel=channel,
        speed_hz=speed_hz,
        size=size,
        rotation=rotation,
        debug=debug,
    )
    # mock_disp_base_init が呼ばれると _conf が設定されるはずだが、
    # DispSpi は コンストラクタ内で _conf を使う場合がある (pin=None の場合)。
    # ヘルパーが pin=None を渡す場合、DispSpi は _conf を参照しようとして
    # mock_disp_base_init が _conf をセットしていないと失敗する可能性がある。
    # しかし現在の mock_disp_base_init は _conf をセットしない。
    # 通常のテストケースでは pin != None で呼び出されるので問題ない。

    return display


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
    mock_sleep.assert_has_calls([call(0.01), call(0.01), call(0.5)])

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

        assert mock_pi_instance.stop.call_count == 2
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
        assert mock_pi_instance.stop.call_count == 2
        mock_super_close.assert_called_once()
        mock_pi_instance.set_PWM_dutycycle.assert_any_call(disp.pin.bl, 255)


def test_set_brightness_no_bl_pin(mock_pi_instance, mock_disp_base_init):
    """set_brightness()のテスト (BLピンなし)."""
    no_bl_pin = SpiPins(rst=11, dc=10, bl=None)
    disp = create_disp_spi_instance(pin=no_bl_pin)

    mock_pi_instance.set_PWM_dutycycle.reset_mock()

    disp.set_brightness(128)
    # BLピンがないのでPWM制御は呼ばれない
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()


def test_set_backlight_no_bl_pin(mock_pi_instance, mock_disp_base_init):
    """set_backlight()のテスト (BLピンなし)."""
    no_bl_pin = SpiPins(rst=11, dc=10, bl=None)
    disp = create_disp_spi_instance(pin=no_bl_pin)

    mock_pi_instance.set_PWM_dutycycle.reset_mock()

    disp.set_backlight(True)
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()

    disp.set_backlight(False)
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()


def test_close_spi_close_error(
    mock_pi_instance, mock_disp_base_init, mock_logger
):
    """close時にspi_closeが例外を投げても処理が継続することを確認."""
    with patch.object(DispBase, "close") as mock_super_close:
        mock_pi_instance.spi_close.side_effect = RuntimeError("SPI Error")

        disp = create_disp_spi_instance()
        disp.pi.connected = True
        disp.spi_handle = 0

        disp.close()

        # エラーログが出て、super().close() までは到達する
        mock_logger.warning.assert_called()
        mock_super_close.assert_called_once()


def test_close_not_connected(
    mock_pi_instance, mock_disp_base_init, mock_logger
):
    """connected=False時のclose動作."""
    with patch.object(DispBase, "close") as mock_super_close:
        disp = create_disp_spi_instance()
        disp.pi.connected = False

        disp.close()

        # spi_close や backlight 制御は呼ばれない
        mock_pi_instance.spi_close.assert_not_called()
        mock_pi_instance.set_PWM_dutycycle.assert_not_called()

        # 警告ログが出る
        mock_logger.warning.assert_called_with("pi.connected=%s", False)
        mock_super_close.assert_called_once()


def test_init_with_conf_pins(mock_pi_instance, mock_disp_base_init):
    """設定ファイルからピン配置を読み込むテスト."""

    # DispBase.__init__ のモックで _conf を注入する必要があるが、
    # DispSpi.__init__ 内で self._conf.data を参照している。
    # mock_disp_base_init は DispBase.__init__ をモックしているが、
    # 呼び出し元の DispSpi インスタンス (obj_self) に対して属性を設定している。

    # DispBase.__init__ は super().__init__ で呼ばれる。
    # その後、DispSpi は self._conf を使う。
    # mock_disp_base_init で obj_self._conf を設定してあげる必要がある。

    with patch(
        "pi0disp.disp.disp_base.MyConf"
    ):  # ここでのPatchはDispBase内でのimportに依存
        # しかし DispSpi は DispBase を継承しており、DispBase.__init__ を呼ぶ。
        # 今回 DispBase.__init__ は mock_disp_base_init で完全に置き換えられている。
        # なので、mock_disp_base_init 内で `obj_self._conf` をセットするように振る舞いを変えるか、
        # ここで `MyConf` を使って手動でセットする。

        # mock_disp_base_init を少し拡張するのは難しいので、
        # DispSpi.__init__ の pin=None ルートを通すために、
        # DispSpiインスタンスが作られる過程で _conf が利用可能になっている必要がある。

        # 実装を見ると:
        # super().__init__(...)  <-- ここで self._conf が生成される (はずだがモックされている)
        # if pin is None:
        #    ... self._conf.data ...

        # したがって、mock_disp_base_init が呼ばれたときに _conf をセットするように副作用を追加する。
        # しかし mock_disp_base_init は fixture なので、ここだけ挙動を変えるのは少し手間。
        # 既存の mock_disp_base_init は _conf をセットしていない (コードを見ると)。
        # DispSpi のテストでは今まで self._conf を使っていなかったから問題なかった。

        # 戦略: mock_disp_base_init の side_effect をラップするか、
        # DispSpi.__init__ の内部実装に踏み込んで self._conf を事前に用意するのは無理（__init__実行中なので）。

        # fixture を使わずに個別に patch するのが正攻法だが、
        # ここでは mock_disp_base_init が返す mock オブジェクトの side_effect を上書き更新する。

        original_side_effect = mock_disp_base_init.side_effect

        # モックデータ構築
        mock_conf_data = MagicMock()
        # self._conf.data.get("spi").get("rst") -> 11
        # self._conf.data.spi.get("rst") -> 11

        mock_spi_conf = MagicMock()
        mock_spi_conf.get.side_effect = lambda k: {
            "rst": 11,
            "dc": 12,
            "bl": 13,
            "cs": 8,
        }.get(k)

        mock_conf_data.get.side_effect = (
            lambda k: mock_spi_conf if k == "spi" else None
        )

        # attribute access: self._conf.data.spi
        type(mock_conf_data).spi = PropertyMock(return_value=mock_spi_conf)

        mock_conf = MagicMock()
        mock_conf.data = mock_conf_data

        def custom_init_side_effect(obj_self, *args, **kwargs):
            original_side_effect(obj_self, *args, **kwargs)
            obj_self._conf = mock_conf

        mock_disp_base_init.side_effect = custom_init_side_effect

        # テスト実行
        # create_disp_spi_instance ヘルパーを使うと pin=None が DEFAULT_PIN に置換されるため
        # 直接コンストラクタを呼ぶ
        disp = DispSpi(pin=None)

        # 確認
        expected_pin = SpiPins(rst=11, dc=12, bl=13, cs=8)
        assert disp.pin == expected_pin

        # side_effect を元に戻す (他のテストへの影響回避)
        mock_disp_base_init.side_effect = original_side_effect


def test_init_with_conf_pins_partial(mock_pi_instance, mock_disp_base_init):
    """設定ファイルからピン配置を読み込むテスト (一部欠損)."""
    original_side_effect = mock_disp_base_init.side_effect

    mock_conf_data = MagicMock()
    mock_spi_conf = MagicMock()
    # "bl" が設定にないケース
    mock_spi_conf.get.side_effect = lambda k: {
        "rst": 11,
        "dc": 12,
        "cs": 8,
    }.get(k)

    mock_conf_data.get.side_effect = (
        lambda k: mock_spi_conf if k == "spi" else None
    )
    type(mock_conf_data).spi = PropertyMock(return_value=mock_spi_conf)

    mock_conf = MagicMock()
    mock_conf.data = mock_conf_data

    def custom_init_side_effect(obj_self, *args, **kwargs):
        original_side_effect(obj_self, *args, **kwargs)
        obj_self._conf = mock_conf

    mock_disp_base_init.side_effect = custom_init_side_effect

    disp = DispSpi(pin=None)

    # bl はデフォルト(23)が使われるはず
    expected_pin = SpiPins(rst=11, dc=12, bl=23, cs=8)
    assert disp.pin == expected_pin

    mock_disp_base_init.side_effect = original_side_effect


def test_set_brightness_bl_off(mock_pi_instance, mock_disp_base_init):
    """バックライトOFF時の set_brightness() テスト."""
    disp = create_disp_spi_instance()
    # 初期状態は backlight_on = False
    assert not disp._backlight_on

    mock_pi_instance.set_PWM_dutycycle.reset_mock()

    disp.set_brightness(100)

    # 値は保持される
    assert disp._brightness == 100
    # しかしPWM制御はされない
    mock_pi_instance.set_PWM_dutycycle.assert_not_called()


def test_close_invalid_spi_handle(mock_pi_instance, mock_disp_base_init):
    """spi_handle < 0 の場合の close() テスト."""
    with patch.object(DispBase, "close") as mock_super_close:
        disp = create_disp_spi_instance()
        disp.pi.connected = True
        disp.spi_handle = -1  # Invalid handle

        disp.close()

        # spi_close は呼ばれない
        mock_pi_instance.spi_close.assert_not_called()
        mock_super_close.assert_called_once()


def test_close_no_backlight_pin(mock_pi_instance, mock_disp_base_init):
    """Backlight pin が None の場合の close() テスト."""
    with patch.object(DispBase, "close") as mock_super_close:
        no_bl_pin = SpiPins(rst=11, dc=10, bl=None)
        # create_helpers will replace pin=None but here we pass specific pin struct
        disp = create_disp_spi_instance(pin=no_bl_pin)
        disp.pi.connected = True
        disp.spi_handle = 0

        disp.close()

        # set_backlight 関連(PWM)は呼ばれない
        mock_pi_instance.set_PWM_dutycycle.assert_not_called()
        mock_super_close.assert_called_once()


def test_close_explicit_bl_switch_true(mock_pi_instance, mock_disp_base_init):
    """close(bl_switch=True) のテスト."""
    with patch.object(DispBase, "close") as mock_super_close:
        disp = create_disp_spi_instance()
        disp.pi.connected = True

        # Explicitly pass True
        disp.close(bl_switch=True)

        mock_pi_instance.set_PWM_dutycycle.assert_called_with(
            disp.pin.bl, 255
        )
        mock_super_close.assert_called_once()
