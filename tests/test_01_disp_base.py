"""Tests for DispBase."""

from unittest.mock import MagicMock, PropertyMock, patch

import pytest
from PIL import Image

from pi0disp import DispBase, DispSize

# Constants
DEFAULT_SIZE = DispSize(240, 320)
DEFAULT_ROTATION = DispBase.DEF_ROTATION


def create_disp_base_instance(
    size: DispSize | None = None,
    rotation: int | None = None,
    debug: bool = False,
) -> DispBase:
    """Helper to create DispBase instance."""
    if size is None:
        size = DEFAULT_SIZE
    if rotation is None:
        raise ValueError("rotation must be specified")
    return DispBase(size=size, rotation=rotation, debug=debug)


def test_init_success(mock_pi_constructor, mock_logger, mock_pi_instance):
    """インスタンス化が成功するケースのテスト."""
    disp_base = create_disp_base_instance(
        size=DEFAULT_SIZE, rotation=DEFAULT_ROTATION, debug=False
    )

    mock_pi_constructor.assert_called_once()
    mock_logger.assert_called_once_with("DispBase", False)
    assert disp_base.pi.connected

    # DispBase.__init__でrotationが考慮される
    assert disp_base.size.width == DEFAULT_SIZE.width
    assert disp_base.size.height == DEFAULT_SIZE.height

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
    disp_base.rotation = 90
    assert disp_base.size.width == DEFAULT_SIZE.height
    assert disp_base.size.height == DEFAULT_SIZE.width
    assert disp_base._rotation == 90


def test_set_rotation_to_0(mock_pi_instance):
    """rotationを0度回転（元に戻す）したときのsizeの変更をテスト."""
    # 初期状態を90度回転にしてから0度に戻すシナリオをテスト
    initial_rotation = 90
    disp_base = create_disp_base_instance(rotation=initial_rotation)
    # 90度回転しているので、widthとheightがスワップされている状態を想定
    assert disp_base.size.width == DEFAULT_SIZE.height
    assert disp_base.size.height == DEFAULT_SIZE.width

    disp_base.rotation = 0
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


def test_init_with_conf_size(mock_pi_constructor, mock_pi_instance):
    """設定ファイルからサイズを読み込むテスト."""
    with patch("pi0disp.disp.disp_base.MyConf") as MockMyConf:
        mock_conf_instance = MockMyConf.return_value

        # data プロパティが返すモックオブジェクトを設定
        mock_data = MagicMock()

        # .get() メソッドの挙動を設定
        def get_side_effect(key):
            if key == "width":
                return 100
            if key == "height":
                return 200
            return None

        mock_data.get.side_effect = get_side_effect

        # 属性アクセスの設定
        type(mock_data).width = PropertyMock(return_value=100)
        type(mock_data).height = PropertyMock(return_value=200)

        mock_conf_instance.data = mock_data

        # size=None で初期化
        # create_disp_base_instance ヘルパーは size=None だと DEFAULT_SIZE を設定してしまうので、
        # 設定ファイルからの読み込みをテストする場合は直接 DispBase を呼ぶ必要がある
        disp_base = DispBase(
            size=None, rotation=DEFAULT_ROTATION, debug=False
        )

        assert disp_base.size.width == 100
        assert disp_base.size.height == 200
        assert disp_base.native_size == DispSize(100, 200)


def test_init_with_conf_rotation(mock_pi_constructor, mock_pi_instance):
    """設定ファイルから回転を読み込むテスト."""
    with patch("pi0disp.disp.disp_base.MyConf") as MockMyConf:
        mock_conf_instance = MockMyConf.return_value

        mock_data = MagicMock()
        mock_data.get.side_effect = lambda k: 180 if k == "rotation" else None
        type(mock_data).rotation = PropertyMock(return_value=180)

        mock_conf_instance.data = mock_data

        # rotation=None で初期化
        # create_disp_base_instance ヘルパーは rotation=None だとエラーになるので直接 DispBase を呼ぶ
        disp_base = DispBase(size=DEFAULT_SIZE, rotation=None)

        assert disp_base.rotation == 180


def test_init_defaults(mock_pi_constructor, mock_pi_instance):
    """引数なし・設定ファイルなしの場合にデフォルト値が使われるテスト."""
    with patch("pi0disp.disp.disp_base.MyConf") as MockMyConf:
        mock_conf_instance = MockMyConf.return_value

        mock_data = MagicMock()
        mock_data.get.return_value = None
        mock_conf_instance.data = mock_data

        disp_base = DispBase(size=None, rotation=None)

        assert disp_base.size == DispBase.DEF_SIZE
        assert disp_base.rotation == DispBase.DEF_ROTATION


def test_context_manager(mock_pi_constructor, mock_pi_instance, mock_logger):
    """コンテキストマネージャ (__enter__, __exit__) のテスト."""

    with DispBase(size=DEFAULT_SIZE, rotation=DEFAULT_ROTATION) as disp:
        assert isinstance(disp, DispBase)
        # __enter__ でログが出るはず
        mock_logger.return_value.debug.assert_called()

    # __exit__ で close が呼ばれ、pi.stop() が実行される
    mock_pi_instance.stop.assert_called_once()
    # __exit__ でもログが出る
    assert mock_logger.return_value.debug.call_count >= 2


def test_properties(mock_pi_instance):
    """プロパティのテスト."""
    disp_base = create_disp_base_instance(
        size=DispSize(100, 200), rotation=90
    )

    # native_size
    assert disp_base.native_size == DispSize(100, 200)

    # conf
    assert disp_base.conf is not None

    # rotation settter logic check (initially 90)
    # 90度なので width/height が swap されているはず
    assert disp_base.size == DispSize(200, 100)

    # rotation 変更 (180) -> swap 解除
    disp_base.rotation = 180
    assert disp_base.rotation == 180
    assert disp_base.size == DispSize(100, 200)

    # rotation 変更 (270) -> swap
    disp_base.rotation = 270
    assert disp_base.rotation == 270
    assert disp_base.size == DispSize(200, 100)
