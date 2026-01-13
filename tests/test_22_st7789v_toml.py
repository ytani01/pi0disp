"""Tests for ST7789V configuration via TOML."""

from unittest.mock import MagicMock, patch

from pi0disp.disp.st7789v import ST7789V


def test_st7789v_toml_loading(mock_pi_instance):
    """TOMLから設定が読み込まれることをテスト."""
    # 階層的な辞書構造をモック
    config_dict = {
        "width": 123,
        "height": 456,
        "invert": False,
        "rotation": 180,
        "x_offset": 10,
        "y_offset": 20,
        "rgb": False,
        "spi": {
            "cs": 8,
            "rst": 25,
            "dc": 24,
            "bl": 23,
            "channel": 0,
            "speed_hz": 40000000,
        },
    }

    mock_data = MagicMock()
    # .get() への対応
    mock_data.get.side_effect = lambda k, default=None: config_dict.get(k, default)
    # .width, .height, .rotation 等の属性アクセスへの対応
    mock_data.width = config_dict["width"]
    mock_data.height = config_dict["height"]
    mock_data.rotation = config_dict["rotation"]
    mock_data.x_offset = config_dict["x_offset"]
    mock_data.y_offset = config_dict["y_offset"]

    # rgb/bgr のハンドリング (in 演算子と辞書アクセス)
    mock_data.__contains__.side_effect = lambda k: k in config_dict
    mock_data.__getitem__.side_effect = lambda k: config_dict[k]

    with patch("pi0disp.disp.disp_base.MyConf") as mock_myconf_class:
        mock_myconf_instance = MagicMock()
        mock_myconf_instance.data = mock_data
        mock_myconf_class.return_value = mock_myconf_instance

        # 引数なしで初期化 -> TOMLの値が使われるはず
        disp = ST7789V()

        assert disp.native_size.width == 123
        assert disp.native_size.height == 456
        assert disp._invert is False
        assert disp._bgr is True  # rgb=False なので bgr=True
        assert disp._x_offset == 10
        assert disp._y_offset == 20
        assert disp.rotation == 180


def test_st7789v_args_priority(mock_pi_instance):
    """TOMLよりもコンストラクタ引数が優先されることをテスト."""
    mock_data = MagicMock()
    config_dict = {"invert": False, "spi": {}}
    mock_data.get.side_effect = lambda k, default=None: config_dict.get(k, default)
    mock_data.__contains__.return_value = False

    with patch("pi0disp.disp.disp_base.MyConf") as mock_myconf_class:
        mock_myconf_instance = MagicMock()
        mock_myconf_instance.data = mock_data
        mock_myconf_class.return_value = mock_myconf_instance

        # TOMLは invert=False だが、引数で invert=True を指定
        disp = ST7789V(invert=True, bgr=False)

        assert disp._invert is True
        assert disp._bgr is False
