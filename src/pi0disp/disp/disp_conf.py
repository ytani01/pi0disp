#
# (c) 2025 Yoichi Tanibayashi
#
import os
from typing import Any, Dict, Optional

from dynaconf import Dynaconf
from dynaconf.vendor.tomllib import TOMLDecodeError

from ..utils.mylogger import errmsg, get_logger  # type: ignore


class DispConf:
    """
    ディスプレイ設定を管理するクラス。
    設定ファイルを読み込み、アクセスを提供する。
    """

    SETTINGS_PATH = ["/etc", "~", "."]
    SETTINGS_EXT = "toml"

    def __init__(self, conf_filename: str | None = None, debug: bool = False):
        """
        ディスプレイ設定のコンストラクタ。
        設定ファイルのパスを構築し、読み込みを試みる。

        パラメータ:
            conf_filename (str | None): 読み込む設定ファイル名 (拡張子を除く)。
                                        指定しない場合、パッケージ名を使用。
            debug (bool): デバッグモードを有効にするか。Trueの場合、詳細なログが出力される。
        """
        self.__debug: bool = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)

        self._pkg_name = __package__.split(".", 1)[0]
        self.__log.debug("_pkg_name=%s", self._pkg_name)

        if conf_filename:
            self._conf_filename = conf_filename
        else:
            self._conf_filename = self._pkg_name
        self.__log.debug("_conf_filename=%s", self._conf_filename)

        self._settings_files = [
            os.path.expandvars(
                os.path.expanduser(
                    f"{p}/{self._conf_filename}.{self.SETTINGS_EXT}"
                )
            )
            for p in self.SETTINGS_PATH
        ]
        self.__log.debug("_settings_files=%s", self._settings_files)

        self._data: Optional[Dynaconf] = self.load(
            self._settings_files, self._pkg_name
        )

    @property
    def pkg_name(self):
        """パッケージ名を返す。"""
        return self._pkg_name

    @property
    def conf_filename(self):
        """読み込む設定ファイル名を返す。"""
        return self._conf_filename

    @property
    def data(self):
        """読み込まれた設定データ (Dynaconfオブジェクト) を返す。"""
        return self._data

    def load(
        self,
        settings_files: list[str] | None = None,
        pkg_name: str | None = None,
    ) -> Optional[Dynaconf]:
        """
        指定された設定ファイルからDynaconf設定を読み込む。

        パラメータ:
            settings_files (list[str] | None): 読み込む設定ファイルのパスリスト。
                                            指定しない場合、_settings_filesを使用。
            pkg_name (str | None): 設定を読み込むパッケージ名。指定しない場合、_pkg_nameを使用。

        戻り値:
            Optional[Dynaconf]: 読み込まれた設定オブジェクト、または読み込みに失敗した場合はNone。
        """
        if not settings_files:
            settings_files = self._settings_files

        if not pkg_name:
            pkg_name = self._pkg_name

        self.__log.debug(
            "settings_files=%s, pkg_name=%s", settings_files, pkg_name
        )

        try:
            return Dynaconf(settings_files=settings_files).get(self._pkg_name)

        except TOMLDecodeError as e:
            self.__log.error("%s: 設定がロードできません。", errmsg(e))
            return None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """
        設定データを辞書形式で返す。

        戻り値:
            Optional[Dict[str, Any]]: 設定データの辞書、または設定データがない場合はNone。
        """
        if self._data:
            return self._data.to_dict()
        return None
