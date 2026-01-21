#
# (c) 2025 Yoichi Tanibayashi
#
import os
from typing import Any, Dict, Optional

import tomlkit
from dynaconf import Dynaconf
from dynaconf.vendor.tomllib import TOMLDecodeError

from ..utils.mylogger import errmsg, get_logger  # type: ignore


def update_toml_settings(
    settings: Dict[str, Any], conf_file: str = "pi0disp.toml"
) -> None:
    """
    Updates or creates a TOML configuration file with the given settings.
    Maintains existing comments and structure where possible.

    Args:
        settings: A dictionary of settings to update (e.g., {"bgr": True}).
        conf_file: Path to the TOML file.
    """
    if os.path.exists(conf_file):
        with open(conf_file, "r") as f:
            data = tomlkit.parse(f.read())
    else:
        data = tomlkit.document()

    if "pi0disp" not in data:
        data.add("pi0disp", tomlkit.table())

    table = data["pi0disp"]
    for key, value in settings.items():
        table[key] = value

    with open(conf_file, "w") as f:
        f.write(tomlkit.dumps(data))



class MyConf:
    """Display Configuration."""

    SETTINGS_PATH = [".", "~", "/etc"]
    SETTINGS_EXT = "toml"

    def __init__(self, conf_filename: str | None = None, debug: bool = False):
        self.__debug: bool = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)

        self._pkg_name = (__package__ or "pi0disp").split(".", 1)[0]
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
            return Dynaconf(settings_files=settings_files).get(pkg_name)

        except TOMLDecodeError as e:
            self.__log.error("%s: configuration is not loaded.", errmsg(e))
            return None

    def to_dict(self) -> Optional[Dict[str, Any]]:
        """To dict."""
        if self._data:
            return self._data.to_dict()
        return None
