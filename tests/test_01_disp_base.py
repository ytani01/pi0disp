"""Tests for DispBase."""

from unittest.mock import MagicMock

import pytest
from PIL import Image

from pi0disp.disp.disp_base import DispBase, Size

DEFAULT_SIZE = Size(240, 320)
DEFAULT_ROTATION = DispBase.DEF_ROTATION


def create_disp_base_instance(
    size: Size | None = None, rotation: int | None = None, debug: bool = False
) -> DispBase:
    """Helper to create DispBase instance."""
    if size is None:
        size = DEFAULT_SIZE
    if rotation is None:
        raise ValueError("rotation must be specified")
    return DispBase(size, rotation, debug)


def test_init_success(mock_pi_constructor, mock_logger, mock_pi_instance):
    """インスタンス化が成功するケースのテスト."""
    disp_base = create_disp_base_instance(
        size=DEFAULT_SIZE, rotation=DEFAULT_ROTATION, debug=False
    )

    mock_pi_constructor.assert_called_once()
    mock_logger.assert_called_once_with("DispBase", False)
    assert disp_base.pi.connected

    # DispBase.__init__でrotationが考慮され、sizeがスワップされる
    assert disp_base.size.width == DEFAULT_SIZE.height
    assert disp_base.size.height == DEFAULT_SIZE.width

    assert disp_base._native_size == DEFAULT_SIZE
    assert disp_base._rotation == DEFAULT_ROTATION


def test_init_pigpio_connection_error(mock_pi_constructor, mock_pi_instance):
    """pigpioへの接続失敗時にRuntimeErrorを送出するテスト."""
    mock_pi_instance.connected = False

    with pytest.raises(RuntimeError) as excinfo:
        create_disp_base_instance(
            size=DEFAULT_SIZE, rotation=DEFAULT_ROTATION
        )
    assert "Could not connect to pigpio daemon" in str(excinfo.value)
    mock_pi_constructor.assert_called_once()


def test_init_display(mock_logger, mock_pi_instance):
    """init_displayが警告ログを出すことをテスト."""
    mock_logger_instance = MagicMock()
    mock_logger.return_value = mock_logger_instance

    disp_base = create_disp_base_instance(rotation=0)
    disp_base.init_display()

    mock_logger_instance.warning.assert_called_once_with(
        "Please override this method."
    )


def test_set_rotation_to_90(mock_pi_instance):
    """set_rotationで90度回転したときのsizeの変更をテスト."""
    disp_base = create_disp_base_instance(rotation=0)
    disp_base.set_rotation(90)
    assert disp_base.size.width == DEFAULT_SIZE.height
    assert disp_base.size.height == DEFAULT_SIZE.width
    assert disp_base._rotation == 90


def test_set_rotation_to_0(mock_pi_instance):
    """set_rotationで0度回転（元に戻す）したときのsizeの変更をテスト."""
    # 初期状態を90度回転にしてから0度に戻すシナリオをテスト
    initial_rotation = 90
    disp_base = create_disp_base_instance(rotation=initial_rotation)
    # 90度回転しているので、widthとheightがスワップされている状態を想定
    assert disp_base.size.width == DEFAULT_SIZE.height
    assert disp_base.size.height == DEFAULT_SIZE.width

    disp_base.set_rotation(0)
    assert disp_base.size.width == DEFAULT_SIZE.width
    assert disp_base.size.height == DEFAULT_SIZE.height
    assert disp_base._rotation == 0


def test_display_resizes_image(mock_pi_instance):
    """displayが画像をリサイズするかをテスト."""
    disp_base = create_disp_base_instance(rotation=DEFAULT_ROTATION)

    mock_image = MagicMock(spec=Image.Image)
    mock_image.size = (100, 100)

    disp_base.display(mock_image)

    expected_size = disp_base.size
    mock_image.resize.assert_called_once_with(expected_size)


def test_display_with_correct_size_image(mock_pi_instance):
    """displayが画像のリサイズをしないことをテスト（サイズが既に正しい場合）."""
    disp_base = create_disp_base_instance(rotation=DEFAULT_ROTATION)

    mock_image = MagicMock(spec=Image.Image)
    mock_image.size = disp_base.size

    disp_base.display(mock_image)

    mock_image.resize.assert_not_called()


def test_close_calls_pi_stop_when_connected(mock_pi_instance):
    """connected=Trueの場合にcloseがpi.stop()を呼び出すかをテスト."""
    disp_base = create_disp_base_instance(rotation=0)

    disp_base.close()
    mock_pi_instance.stop.assert_called_once()


def test_close_does_not_call_pi_stop_when_not_connected(mock_pi_instance):
    """connected=Falseの場合にcloseがpi.stop()を呼び出さないかをテスト."""
    disp_base = create_disp_base_instance(rotation=0)

    # テストしたい条件（connected=False）をインスタンス化後に設定
    disp_base.pi.connected = False

    disp_base.close()
    mock_pi_instance.stop.assert_not_called()
