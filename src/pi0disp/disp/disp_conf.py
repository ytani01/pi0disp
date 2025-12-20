#
# (c) 2025 Yoichi Tanibayashi
#
import os
from typing import Any, Dict, Optional

from dynaconf import Dynaconf
from dynaconf.vendor.tomllib import TOMLDecodeError

from ..utils.mylogger import errmsg, get_logger  # type: ignore


class DispConf:
    """Display Configuration."""

    SETTINGS_PATH = ["/etc", "~", "."]
    SETTINGS_EXT = "toml"

    def __init__(self, conf_filename: str | None = None, debug: bool = False):
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
        """package name"""
        return self._pkg_name

    @property
    def conf_filename(self):
        """Config filename"""
        return self._conf_filename

    @property
    def data(self):
        """configuration data."""
        return self._data

    def load(
        self,
        settings_files: list[str] | None = None,
        pkg_name: str | None = None,
    ) -> Optional[Dynaconf]:
        """Load configuration."""
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
            self.__log.error("%s: configuration is not loaded.", errmsg(e))
            return None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """To dict."""
        if self._data:
            return self._data.to_dict()
        return None
