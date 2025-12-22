"""Tests for MyConf."""

from unittest.mock import MagicMock, patch

from dynaconf.vendor.tomllib import TOMLDecodeError

from pi0disp.utils.my_conf import MyConf


class TestMyConf:
    """Tests for MyConf class."""

    @patch("pi0disp.utils.my_conf.Dynaconf")
    def test_init_defaults(self, mock_dynaconf):
        """デフォルト初期化のテスト."""
        # Setup mock
        mock_instance = MagicMock()
        mock_dynaconf.return_value = mock_instance
        # get() returns the config object
        mock_config = MagicMock()
        mock_instance.get.return_value = mock_config

        conf = MyConf()

        # Check basic properties
        assert conf.pkg_name == "pi0disp"
        assert conf.conf_filename == "pi0disp"

        # Check settings files construction
        # Expecting path expansion to work generally, but here we just check if list is created
        assert isinstance(conf._settings_files, list)
        assert len(conf._settings_files) == 3
        assert conf.data == mock_config

        # Check Dynaconf call
        mock_dynaconf.assert_called_once()
        mock_instance.get.assert_called_with("pi0disp")

    @patch("pi0disp.utils.my_conf.Dynaconf")
    def test_init_custom_filename(self, mock_dynaconf):
        """ファイル名指定時の初期化テスト."""
        mock_instance = MagicMock()
        mock_dynaconf.return_value = mock_instance
        mock_config = MagicMock()
        mock_instance.get.return_value = mock_config

        conf = MyConf(conf_filename="myparams", debug=True)

        assert conf.conf_filename == "myparams"
        # Check if filename is in settings paths
        assert any("myparams.toml" in p for p in conf._settings_files)
        assert conf.data == mock_config

    @patch("pi0disp.utils.my_conf.Dynaconf")
    def test_load_success(self, mock_dynaconf):
        """load成功時のテスト."""
        mock_instance = MagicMock()
        mock_dynaconf.return_value = mock_instance
        mock_config = MagicMock()
        mock_instance.get.return_value = mock_config

        conf = MyConf()

        # Manually call load
        files = ["/tmp/test.toml"]
        pkg = "testpkg"
        result = conf.load(settings_files=files, pkg_name=pkg)

        mock_dynaconf.assert_called_with(settings_files=files)
        mock_instance.get.assert_called_with(pkg)
        assert result == mock_config

    @patch("pi0disp.utils.my_conf.Dynaconf")
    def test_load_toml_error(self, mock_dynaconf):
        """TOMLデコードエラー時のテスト."""
        mock_instance = MagicMock()
        mock_dynaconf.return_value = mock_instance
        # get() raises TOMLDecodeError
        mock_instance.get.side_effect = TOMLDecodeError("Invalid TOML")

        conf = MyConf()

        # data should be None because init calls load which fails
        assert conf.data is None

        # Manual load call
        result = conf.load()
        assert result is None

    def test_to_dict_success(self):
        """to_dict成功時のテスト."""
        with patch("pi0disp.utils.my_conf.Dynaconf") as mock_dynaconf:
            mock_instance = MagicMock()
            mock_dynaconf.return_value = mock_instance
            mock_config = MagicMock()
            mock_config.to_dict.return_value = {"key": "value"}
            mock_instance.get.return_value = mock_config

            conf = MyConf()
            assert conf.to_dict() == {"key": "value"}

    def test_to_dict_none(self):
        """dataがNoneの場合のto_dictテスト."""
        with patch("pi0disp.utils.my_conf.Dynaconf") as mock_dynaconf:
            # Simulate load failure
            mock_instance = MagicMock()
            mock_dynaconf.return_value = mock_instance
            mock_instance.get.side_effect = TOMLDecodeError("Error")

            conf = MyConf()
            assert conf.data is None
            assert conf.to_dict() is None

    def test_properties(self):
        """各プロパティのテスト."""
        with patch("pi0disp.utils.my_conf.Dynaconf"):
            conf = MyConf()
            assert conf.pkg_name == conf._pkg_name
            assert conf.conf_filename == conf._conf_filename
            assert conf.data == conf._data
