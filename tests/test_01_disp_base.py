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


def test_init_with_debug_true(mock_pi_constructor, mock_logger, mock_pi_instance):
    """debug=TrueでDispBaseをインスタンス化した場合にロガーがデバッグログを出力することをテスト."""
    disp_base = create_disp_base_instance(
        size=DEFAULT_SIZE, rotation=DEFAULT_ROTATION, debug=True
    )

    mock_pi_constructor.assert_called_once()
    mock_logger.assert_called_once_with("DispBase", True)
    assert disp_base.pi.connected

    # 初期化時のデバッグログが出力されたことを確認
    # _log.debug("size=%s,rotation=%s", size, rotation)
    mock_logger.return_value.debug.assert_any_call(
        "size=%s,rotation=%s", DEFAULT_SIZE, DEFAULT_ROTATION
    )


def test_init_pigpio_connection_error(mock_pi_constructor, mock_pi_instance):
    """pigpioへの接続失敗時にRuntimeErrorを送出するテスト."""
    mock_pi_instance.connected = False

    with pytest.raises(RuntimeError) as excinfo:
        create_disp_base_instance(size=DEFAULT_SIZE, rotation=DEFAULT_ROTATION)
    assert "Could not connect to pigpio daemon" in str(excinfo.value)
    mock_pi_constructor.assert_called_once()


def test_init_display(mock_logger, mock_pi_instance):
    """init_displayが警告ログを出すことをテスト."""
    mock_logger_instance = MagicMock()
    mock_logger.return_value = mock_logger_instance

    disp_base = create_disp_base_instance(rotation=0)
    disp_base.init_display()

    mock_logger_instance.warning.assert_called_once_with(
        "このメソッドはオーバーライドしてください。"
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


def test_set_rotation_to_180(mock_pi_instance):
    """rotationを180度回転したときにsizeの変更がないことをテスト."""
    disp_base = create_disp_base_instance(rotation=0)
    disp_base.rotation = 180
    assert disp_base.size.width == DEFAULT_SIZE.width
    assert disp_base.size.height == DEFAULT_SIZE.height
    assert disp_base._rotation == 180


def test_set_rotation_from_270_to_0(mock_pi_instance):
    """初期回転を270度にしてから0度に戻したときのsizeの変更をテスト."""
    initial_rotation = 270
    disp_base = create_disp_base_instance(rotation=initial_rotation)
    # 270度回転しているので、widthとheightがスワップされている状態を想定
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


def test_display_logs_on_resize(mock_pi_instance, mock_logger):
    """displayが画像をリサイズした場合にデバッグログを出力することをテスト."""
    mock_logger_instance = MagicMock()
    mock_logger.return_value = mock_logger_instance

    disp_base = create_disp_base_instance(rotation=DEFAULT_ROTATION)

    mock_image = MagicMock(spec=Image.Image)
    mock_image.size = (100, 100)  # disp_base.size と異なるサイズ

    disp_base.display(mock_image)

    mock_logger_instance.debug.assert_called_with(
        "画像のサイズをディスプレイに合わせて調整します。"
    )


def test_display_no_logs_on_no_resize(mock_pi_instance, mock_logger):
    """displayが画像をリサイズしない場合にデバッグログを出力しないことをテスト."""
    mock_logger_instance = MagicMock()
    mock_logger.return_value = mock_logger_instance

    disp_base = create_disp_base_instance(rotation=DEFAULT_ROTATION)

    mock_image = MagicMock(spec=Image.Image)
    mock_image.size = disp_base.size  # disp_base.size と同じサイズ

    # 既存のログ呼び出しをリセット
    mock_logger_instance.reset_mock()

    disp_base.display(mock_image)

    mock_logger_instance.debug.assert_not_called()


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
        disp_base = DispBase(size=None, rotation=DEFAULT_ROTATION, debug=False)

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


def test_context_manager_with_exception(
    mock_pi_constructor, mock_pi_instance, mock_logger
):
    """コンテキストマネージャ内で例外が発生した場合でもclose()が呼ばれることをテスト."""
    from unittest.mock import ANY

    with pytest.raises(ValueError, match="Test exception"):
        with DispBase(size=DEFAULT_SIZE, rotation=DEFAULT_ROTATION) as disp:
            assert isinstance(disp, DispBase)
            raise ValueError("Test exception")

        # __exit__ で close が呼ばれ、pi.stop() が実行される
        mock_pi_instance.stop.assert_called_once()
        # __exit__ でもログが出ることを確認（exc_type, exc_val, exc_tbを確認）
        mock_logger.return_value.debug.assert_any_call(
            "exc_type=%s,exc_val=%s,exc_tb=%s",
            ValueError,
            "Test exception",
            ANY,  # exc_tbは動的に生成されるのでANYでマッチさせる
        )


def test_properties(mock_pi_instance):
    """プロパティのテスト."""
    disp_base = create_disp_base_instance(size=DispSize(100, 200), rotation=90)

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


def test_get_display_info_with_conf_values(mock_pi_constructor):
    """get_display_infoがMyConfからwidth, height, rotationを正しく読み込むことをテスト."""
    from pi0disp.disp.disp_base import get_display_info

    with patch("pi0disp.disp.disp_base.MyConf") as MockMyConf:
        mock_conf_instance = MockMyConf.return_value
        mock_data = MagicMock()
        mock_data.get.side_effect = lambda k: {
            "width": 100,
            "height": 200,
            "rotation": 90,
        }.get(k)
        type(mock_data).width = PropertyMock(return_value=100)
        type(mock_data).height = PropertyMock(return_value=200)
        type(mock_data).rotation = PropertyMock(return_value=90)
        mock_conf_instance.data = mock_data

        info = get_display_info(debug=False)

        assert info == {"width": 100, "height": 200, "rotation": 90}
        MockMyConf.assert_called_once_with(debug=False)


def test_get_display_info_with_missing_conf_values(mock_pi_constructor):
    """get_display_infoがMyConfにwidth, height, rotationがない場合にNoneを返すことをテスト."""
    from pi0disp.disp.disp_base import get_display_info

    with patch("pi0disp.disp.disp_base.MyConf") as MockMyConf:
        mock_conf_instance = MockMyConf.return_value
        mock_data = MagicMock()
        mock_data.get.return_value = None  # 全てのキーに対してNoneを返す
        mock_conf_instance.data = mock_data

        info = get_display_info(debug=False)

        assert info == {"width": None, "height": None, "rotation": None}
        MockMyConf.assert_called_once_with(debug=False)


def test_get_display_info_with_debug_true(mock_pi_constructor, mock_logger):
    """get_display_info(debug=True)がデバッグログを出力することをテスト."""
    from pi0disp.disp.disp_base import get_display_info

    mock_logger_instance = MagicMock()
    mock_logger.return_value = mock_logger_instance

    with patch("pi0disp.disp.disp_base.MyConf") as MockMyConf:
        mock_conf_instance = MockMyConf.return_value
        mock_data = MagicMock()
        mock_data.get.return_value = None  # ログ出力のみを確認するため、値はNoneでよい
        mock_conf_instance.data = mock_data

        get_display_info(debug=True)

        MockMyConf.assert_called_once_with(debug=True)
        # ロガーが呼び出され、"read config file" がログ出力されたことを確認
        mock_logger.assert_called_once_with("get_display_info", True)
        mock_logger_instance.debug.assert_any_call("設定ファイルを読み込みます。")
        # ログメッセージの引数を確認
        mock_logger_instance.debug.assert_any_call(
            "width=%s, height=%s, rotation=%s", None, None, None
        )
