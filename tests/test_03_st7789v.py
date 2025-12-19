"""Tests for ST7789V."""

from unittest.mock import MagicMock, patch

import pytest
from PIL import Image

from pi0disp.disp.disp_base import DispBase, DispSize
from pi0disp.disp.disp_spi import SpiPins
from pi0disp.disp.st7789v import ST7789V

# Constants
DEFAULT_SIZE = DispSize(240, 320)
DEFAULT_PIN = SpiPins(rst=25, dc=24, bl=23)
DEFAULT_CHANNEL = 0
DEFAULT_SPEED_HZ = 40_000_000
DEFAULT_ROTATION = DispBase.DEF_ROTATION


@pytest.fixture
def mock_sleep():
    """Mock time.sleep."""
    with patch("time.sleep") as mock:
        yield mock


@pytest.fixture
def mock_optimizer_pack():
    """Mock performance_core.create_optimizer_pack."""
    with patch("pi0disp.disp.st7789v.create_optimizer_pack") as mock:
        # Create mock objects for the pack
        pack = {
            "memory_pool": MagicMock(),
            "region_optimizer": MagicMock(),
            "performance_monitor": MagicMock(),
            "adaptive_chunking": MagicMock(),
            "color_converter": MagicMock(),
        }

        # Setup behavior for specific optimizers to avoid runtime errors
        pack["adaptive_chunking"].get_chunk_size.return_value = 4096

        # Mock color converter to return dummy bytes
        def _dummy_rgb_to_rgb565_bytes(arr):
            # Return bytes equal to array size * 2 (16bit)
            return b"\x00" * (arr.shape[0] * arr.shape[1] * 2)

        pack[
            "color_converter"
        ].rgb_to_rgb565_bytes.side_effect = _dummy_rgb_to_rgb565_bytes

        # Region optimizer clamping
        def _dummy_clamp(region, w, h):
            return (
                max(0, region[0]),
                max(0, region[1]),
                min(w, region[2]),
                min(h, region[3]),
            )

        pack["region_optimizer"].clamp_region.side_effect = _dummy_clamp

        mock.return_value = pack
        yield pack


def create_st7789v_instance(
    size: DispSize | None = None,
    rotation: int = DEFAULT_ROTATION,
    bl_at_close: bool = False,
    channel: int = DEFAULT_CHANNEL,
    pin: SpiPins | None = None,
    speed_hz: int = DEFAULT_SPEED_HZ,
    debug: bool = False,
) -> ST7789V:
    """Helper to create ST7789V instance."""
    if size is None:
        size = DEFAULT_SIZE
    if pin is None:
        pin = DEFAULT_PIN

    return ST7789V(
        bl_at_close=bl_at_close,
        channel=channel,
        pin=pin,
        speed_hz=speed_hz,
        size=size,
        rotation=rotation,
        debug=debug,
    )


def test_init_success(
    mock_pi_instance, mock_sleep, mock_optimizer_pack, mock_logger
):
    """初期化成功時のテスト."""
    disp = create_st7789v_instance()

    # 親クラスの初期化確認 (mock_pi_instance等の設定)
    mock_pi_instance.spi_open.assert_called_once()

    # オプティマイザの初期化確認
    assert disp._optimizers == mock_optimizer_pack

    # init_display, set_rotation が呼ばれていることの確認
    # (内部実装依存だが、set_rotationによってMADCTLが呼ばれるはず)
    # ここではコマンド送信の一部を確認
    mock_pi_instance.spi_write.assert_called()


def test_init_display(mock_pi_instance, mock_sleep):
    """init_display()のテスト - ハードウェア初期化シーケンス."""
    disp = create_st7789v_instance()

    # 呼び出し履歴のリセット（__init__で一度呼ばれているため）
    mock_pi_instance.reset_mock()
    mock_sleep.reset_mock()

    disp.init_display()

    # 主要なコマンドが送信されているか確認
    # SWRESET(0x01), SLPOUT(0x11), COLMOD(0x3A), DISPON(0x29) など

    # sleepの呼び出し確認
    # mock_sleep は DispSpi.init_display でも呼ばれている
    assert mock_sleep.call_count >= 3


def test_set_rotation(mock_pi_instance):
    """set_rotation()のテスト."""
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()

    # 0度
    disp.set_rotation(0)

    # 90度
    disp.set_rotation(90)

    # 180度
    disp.set_rotation(180)

    # 270度
    disp.set_rotation(270)

    # 不正な値
    with pytest.raises(ValueError):
        disp.set_rotation(45)


def test_set_window(mock_pi_instance):
    """set_window()のテスト."""
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()

    # 初回呼び出し
    disp.set_window(0, 0, 239, 319)

    # CASET(0x2A), RASET(0x2B), RAMWR(0x2C) が呼ばれる
    # それぞれコマンド送信後にデータ4バイト送信
    assert (
        mock_pi_instance.spi_write.call_count >= 5
    )  # 2 cmds+data + 1 cmd (RAMWR)

    # 違う値で呼び出し
    mock_pi_instance.reset_mock()
    disp.set_window(10, 10, 100, 100)
    assert mock_pi_instance.spi_write.call_count >= 5


def test_write_pixels(mock_pi_instance, mock_optimizer_pack):
    """write_pixels()のテスト."""
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()

    # チャンクサイズ以下のデータ
    small_data = b"\xff" * 100
    disp.write_pixels(small_data)

    mock_pi_instance.write.assert_called_with(disp.pin.dc, 1)  # Data Mode
    mock_pi_instance.spi_write.assert_called_once_with(
        disp.spi_handle, small_data
    )

    # チャンクサイズを超えるデータ (Mockのchunk_sizeは4096)
    large_data = b"\xff" * (4096 * 2 + 100)
    mock_pi_instance.reset_mock()
    disp.write_pixels(large_data)

    assert mock_pi_instance.spi_write.call_count == 3
    # 4096, 4096, 100 バイトで分割送信されるはず


def test_display(mock_pi_instance, mock_optimizer_pack):
    """display()のテスト."""
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()

    # ダミー画像
    image = Image.new("RGB", disp.size, "red")

    with patch.object(disp, "set_window") as mock_set_window:
        with patch.object(disp, "write_pixels") as mock_write_pixels:
            disp.display(image)

            mock_set_window.assert_called_once_with(
                0, 0, disp.size.width - 1, disp.size.height - 1
            )
            mock_write_pixels.assert_called_once()


def test_display_region(mock_pi_instance, mock_optimizer_pack):
    """display_region()のテスト."""
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()

    image = Image.new("RGB", disp.size, "blue")

    with patch.object(disp, "set_window") as mock_set_window:
        with patch.object(disp, "write_pixels") as mock_write_pixels:
            # 有効な領域
            disp.display_region(image, 10, 10, 50, 50)

            mock_set_window.assert_called_once_with(10, 10, 49, 49)
            mock_write_pixels.assert_called_once()

            # 無効な領域 (width <= 0) - clamp_regionの実装はmock次第だが、
            # 実装では clamp_region後にチェックがある
            mock_set_window.reset_mock()
            mock_write_pixels.reset_mock()

            # Mockのclamp_regionは入力をそのままclampして返す
            # ここでは呼び出し側でチェックにかかるような入力を与える
            # region[2] <= region[0] となるケース
            disp.display_region(image, 10, 10, 10, 20)
            mock_set_window.assert_not_called()
            mock_write_pixels.assert_not_called()


def test_power_management(mock_pi_instance):
    """sleep, wake, dispoffのテスト."""
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()

    disp.sleep()
    # SLPIN(0x10), BL=0
    # コマンド送信確認は難しいので、BL制御を確認
    mock_pi_instance.write.assert_called_with(disp.pin.bl, 0)

    disp.wake()
    # SLPOUT(0x11), BL=1
    mock_pi_instance.write.assert_called_with(disp.pin.bl, 1)

    disp.dispoff()
    # DISPOFF(0x28), BL=0
    mock_pi_instance.write.assert_called_with(disp.pin.bl, 0)


def test_close(mock_pi_instance):
    """close()のテスト."""
    disp = create_st7789v_instance()
    mock_pi_instance.reset_mock()

    disp.close()

    mock_pi_instance.spi_close.assert_called_once_with(disp.spi_handle)
    mock_pi_instance.stop.assert_called_once()
