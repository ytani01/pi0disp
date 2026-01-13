import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from dynaconf.vendor.tomllib import TOMLDecodeError

from pi0disp.disp.disp_conf import DispConf


@pytest.fixture
def toml_file_fixture():
    """
    一時的なTOMLファイルを作成し、そのパスを返すフィクスチャ。
    テストの終了時にファイルを削除する。
    """

    def _creator(content: str | None = None, is_valid_toml: bool = True):
        with tempfile.TemporaryDirectory() as tmpdir:
            file_path = Path(tmpdir) / "test_conf.toml"
            if content is not None:
                if is_valid_toml:
                    file_path.write_text(content)
                else:
                    # 無効なTOMLの場合、適当な文字列を書き込む
                    file_path.write_text("this is not a valid toml")
            else:
                # contentがNoneの場合は空ファイルを作成
                file_path.touch()

            yield file_path

    return _creator


@pytest.fixture
def mock_logger():
    """mylogger.get_logger をモックするフィクスチャ."""
    with (
        patch("pi0disp.disp.disp_conf.get_logger") as mock_get_logger,
        patch("pi0disp.disp.disp_conf.errmsg") as mock_errmsg,
    ):  # errmsg もパッチ
        mock_logger_instance = MagicMock()
        mock_get_logger.return_value = mock_logger_instance
        mock_errmsg.side_effect = lambda e: str(
            e
        )  # errmsg はエラーメッセージを文字列化する
        yield mock_get_logger


@pytest.fixture
def mock_os_path():
    """os.path.expanduser と os.path.expandvars をモックするフィクスチャ."""
    with (
        patch("os.path.expanduser") as mock_expanduser,
        patch("os.path.expandvars") as mock_expandvars,
    ):
        mock_expanduser.side_effect = lambda path: path.replace("~", "/home/user")
        mock_expandvars.side_effect = lambda path: path
        yield mock_expanduser, mock_expandvars


class TestDispConf:
    """DispConf クラスのテスト."""

    # _setup_dynaconf_mock は Dynaconf のモック設定を共通化するためのヘルパーメソッド
    def _setup_dynaconf_mock(
        self, mock_dynaconf_class, get_return_value, to_dict_return_value=None
    ):
        mock_dynaconf_instance = MagicMock()
        # get() が呼ばれたときの戻り値を設定
        mock_dynaconf_instance.get.return_value = get_return_value

        if to_dict_return_value is not None:
            mock_dynaconf_instance.to_dict.return_value = to_dict_return_value

        # Dynaconf(...) が呼ばれたら mock_dynaconf_instance を返す
        mock_dynaconf_class.return_value = mock_dynaconf_instance
        return mock_dynaconf_instance

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_init_default_args(self, mock_load, mock_os_path, mock_logger):
        """デフォルト引数で初期化が成功すること."""
        mock_load.return_value = MagicMock()  # load が MagicMock を返すように設定

        disp_conf = DispConf()
        assert disp_conf is not None
        assert disp_conf.pkg_name == "pi0disp"
        assert disp_conf.conf_filename == "pi0disp"
        mock_logger.return_value.debug.assert_called()  # __init__ 内で呼ばれる
        mock_load.assert_called_once()  # load が呼ばれたことを確認

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_init_custom_filename(self, mock_load, mock_os_path, mock_logger):
        """カスタムファイル名での初期化が成功すること."""
        custom_filename = "my_custom_conf"
        mock_load.return_value = MagicMock()

        disp_conf = DispConf(conf_filename=custom_filename)
        assert disp_conf is not None
        assert disp_conf.conf_filename == custom_filename
        mock_logger.return_value.debug.assert_called()  # __init__ 内で呼ばれる
        mock_load.assert_called_once()

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_init_debug_mode(self, mock_load, mock_os_path, mock_logger):
        """debug=True で初期化された場合、ロガーがデバッグモードになっていること."""
        mock_load.return_value = MagicMock()

        DispConf(debug=True)
        # get_logger の呼び出し引数を検証
        mock_logger.assert_called_with("DispConf", True)
        mock_load.assert_called_once()

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_init_no_conf_file(self, mock_load, mock_os_path, mock_logger):
        """設定ファイルが見つからない場合に _data が None になること."""
        mock_load.return_value = None  # load が None を返すように設定

        disp_conf = DispConf()
        assert disp_conf.data is None
        mock_logger.return_value.debug.assert_called()  # __init__ 内で呼ばれる
        # load をモックしているので、load内部のエラーログは出力されない
        mock_load.assert_called_once()

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_init_invalid_toml(self, mock_load, mock_os_path, mock_logger):
        """不正な形式の設定ファイル（TOMLDecodeError）の場合に _data が None になること."""
        mock_load.return_value = None  # load が None を返すように設定（エラー捕捉後）

        disp_conf = DispConf()
        assert disp_conf.data is None
        mock_logger.return_value.debug.assert_called()  # __init__ 内で呼ばれる
        # load をモックしているので、load内部のエラーログは出力されない
        mock_load.assert_called_once()

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_pkg_name_property(self, mock_load, mock_os_path, mock_logger):
        """pkg_name プロパティが正しいパッケージ名を返すこと."""
        mock_load.return_value = MagicMock()

        disp_conf = DispConf()
        assert disp_conf.pkg_name == "pi0disp"
        mock_load.assert_called_once()

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_conf_filename_property(self, mock_load, mock_os_path, mock_logger):
        """conf_filename プロパティが正しい設定ファイル名を返すこと."""
        custom_filename = "my_app_conf"
        mock_load.return_value = MagicMock()

        disp_conf = DispConf(conf_filename=custom_filename)
        assert disp_conf.conf_filename == custom_filename
        mock_load.assert_called_once()

        # デフォルトファイル名の場合
        mock_load.reset_mock()  # mock_load の呼び出し回数をリセット

        disp_conf_default = DispConf()
        assert disp_conf_default.conf_filename == "pi0disp"
        mock_load.assert_called_once()

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_data_property_valid(self, mock_load, mock_os_path, mock_logger):
        """data プロパティが Dynaconf オブジェクトを返すこと（設定が正常に読み込まれた場合).
        Dynaconf が正常に値を返すようにモックする.
        """
        mock_dynaconf_instance_returned = MagicMock()
        # get('key') で 'value' を返すように設定 (辞書全体ではなく値)
        mock_dynaconf_instance_returned.get.side_effect = (
            lambda k: "value" if k == "key" else None
        )

        mock_load.return_value = mock_dynaconf_instance_returned

        disp_conf = DispConf()
        assert disp_conf.data is not None
        assert disp_conf.data == mock_dynaconf_instance_returned
        assert isinstance(
            disp_conf.data, MagicMock
        )  # DispConf.data が MagicMock であることを確認
        assert disp_conf.data.get("key") == "value"

    @patch("pi0disp.disp.disp_conf.DispConf.load")
    def test_data_property_none(self, mock_load, mock_os_path, mock_logger):
        """data プロパティが None を返すこと（設定が読み込まれなかった場合）."""
        mock_load.return_value = None

        disp_conf = DispConf()
        assert disp_conf.data is None

    def test_load_success(self, toml_file_fixture, mock_os_path, mock_logger):
        """有効な設定ファイルパスのリストとパッケージ名で設定を正常に読み込むこと."""
        toml_content = """
        [pi0disp]
        key1 = "value1"
        key2 = 123
        """
        temp_file_path = toml_file_fixture(toml_content, is_valid_toml=True)

        with patch("pi0disp.disp.disp_conf.Dynaconf") as mock_dynaconf_class:
            mock_dynaconf_instance = self._setup_dynaconf_mock(
                mock_dynaconf_class, {"key1": "value1", "key2": 123}
            )
            # get() の戻り値は辞書的なアクセスができるようにする
            mock_dynaconf_instance.get.return_value = {
                "key1": "value1",
                "key2": 123,
            }

            disp_conf_instance = DispConf(conf_filename=None)

            # __init__ での呼び出し分をリセット
            mock_dynaconf_class.reset_mock()
            mock_dynaconf_instance.reset_mock()

            loaded_data = disp_conf_instance.load(
                settings_files=[str(temp_file_path)], pkg_name="pi0disp"
            )

            assert loaded_data is not None
            assert loaded_data["key1"] == "value1"
            assert loaded_data["key2"] == 123
            mock_dynaconf_class.assert_called_once_with(
                settings_files=[str(temp_file_path)]
            )
            # 引数チェック
            mock_dynaconf_instance.get.assert_called_once_with("pi0disp")

    def test_load_default_settings_files(self, mock_os_path, mock_logger):
        """settings_files が None の場合にデフォルトパスを使用することを確認."""
        with patch("pi0disp.disp.disp_conf.Dynaconf") as mock_dynaconf_class:
            mock_dynaconf_instance = self._setup_dynaconf_mock(mock_dynaconf_class, {})

            disp_conf_instance = DispConf(conf_filename="myconf")

            # __init__ での呼び出し分をリセット
            mock_dynaconf_class.reset_mock()
            mock_dynaconf_instance.reset_mock()

            disp_conf_instance.load(settings_files=None, pkg_name="pi0disp")

            expected_settings_files = [
                "/etc/myconf.toml",
                "/home/user/myconf.toml",
                "./myconf.toml",
            ]
            mock_dynaconf_class.assert_called_once_with(
                settings_files=expected_settings_files
            )
            mock_dynaconf_instance.get.assert_called_once_with("pi0disp")

    def test_load_default_pkg_name(self, toml_file_fixture, mock_os_path, mock_logger):
        """pkg_name が None の場合にデフォルトパッケージ名を使用することを確認."""
        toml_content = """
        [my_package]
        key = "value"
        """
        temp_file_path = toml_file_fixture(toml_content, is_valid_toml=True)

        with patch("pi0disp.disp.disp_conf.Dynaconf") as mock_dynaconf_class:
            mock_dynaconf_instance = self._setup_dynaconf_mock(
                mock_dynaconf_class, {"key": "value"}
            )
            mock_dynaconf_instance.get.return_value = {"key": "value"}

            disp_conf_instance = DispConf(conf_filename=None)

            # __init__ での呼び出し分をリセット
            mock_dynaconf_class.reset_mock()
            mock_dynaconf_instance.reset_mock()

            loaded_data = disp_conf_instance.load(
                settings_files=[str(temp_file_path)], pkg_name=None
            )

            assert loaded_data is not None
            assert loaded_data["key"] == "value"
            mock_dynaconf_class.assert_called_once_with(
                settings_files=[str(temp_file_path)]
            )
            mock_dynaconf_instance.get.assert_called_once_with("pi0disp")

    def test_load_invalid_toml_error(
        self, toml_file_fixture, mock_os_path, mock_logger
    ):
        """不正なTOML形式のファイルパスを渡した場合に TOMLDecodeError が捕捉され None が返されること."""
        invalid_toml_content = "this is not a valid toml"
        with tempfile.TemporaryDirectory() as tmpdir:
            temp_file_path = Path(tmpdir) / "invalid_conf.toml"
            temp_file_path.write_text(invalid_toml_content)

            with patch("pi0disp.disp.disp_conf.Dynaconf") as mock_dynaconf_class:
                # Dynaconf(...) の初期化で例外ではなく、.get() 呼び出しなどで例外が出る可能性もあるが
                # 実装を見ると Dynaconf(settings_files=...).get(...) なので
                # Dynaconf(...) 自体は通るかもしれない。
                # ただし実装は `try: return Dynaconf(...)` となっているので、
                # インスタンス生成時のエラーも捕捉される。
                # ここではインスタンス生成時にエラーを出すように設定する。
                mock_dynaconf_class.side_effect = TOMLDecodeError("mock decode error")

                disp_conf_instance = DispConf(conf_filename=None)
                loaded_data = disp_conf_instance.load(
                    settings_files=[str(temp_file_path)], pkg_name="pi0disp"
                )

                assert loaded_data is None
                mock_logger.return_value.error.assert_called()

    def test_to_dict_success(self, toml_file_fixture, mock_os_path, mock_logger):
        """設定が正常に読み込まれた場合、辞書形式で設定データが返されること."""
        toml_content = """
        [pi0disp]
        foo = "bar"
        baz = 123
        """
        temp_file_path = toml_file_fixture(toml_content, is_valid_toml=True)

        with patch("pi0disp.disp.disp_conf.Dynaconf") as mock_dynaconf_class:
            # get() の戻り値として、to_dict() メソッドを持つ Mock オブジェクトを設定する
            mock_data_obj = MagicMock()
            mock_data_obj.to_dict.return_value = {"foo": "bar", "baz": 123}

            _mock_dynaconf_instance = self._setup_dynaconf_mock(
                mock_dynaconf_class,
                mock_data_obj,  # get_return_value
                to_dict_return_value={"foo": "bar", "baz": 123},
            )

            disp_conf_instance = DispConf(conf_filename=None)

            disp_conf_instance.load(
                settings_files=[str(temp_file_path)], pkg_name="pi0disp"
            )

            result_dict = disp_conf_instance.to_dict()

            assert result_dict is not None
            assert isinstance(result_dict, dict)
            assert result_dict["foo"] == "bar"
            assert result_dict["baz"] == 123

    def test_to_dict_none(self, mock_os_path, mock_logger):
        """設定が読み込まれなかった場合（_data が None の場合）、None が返されること."""
        with patch("pi0disp.disp.disp_conf.Dynaconf") as mock_dynaconf_class:
            # get() が None を返すように設定
            mock_dynaconf_instance = self._setup_dynaconf_mock(
                mock_dynaconf_class, None
            )
            mock_dynaconf_instance.get.return_value = None

            disp_conf_instance = DispConf()

            assert disp_conf_instance.data is None
            result_dict = disp_conf_instance.to_dict()
            assert result_dict is None
