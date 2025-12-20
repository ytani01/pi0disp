#
# (c) 2025 Yoichi Tanibayashi
#
import os

from dynaconf import Dynaconf

from ..utils.mylogger import errmsg, get_logger


class DispConf:
    """Display Configuration."""

    SETTINGS_PATH = ["/etc", "~", "."]
    SETTINGS_EXT = "toml"

    def __init__(self, debug: bool = False):
        self.__debug: bool = debug
        self.__log = get_logger(self.__class__.__name__, self.__debug)

        self._pkg_name = __package__.split(".", 1)[0]
        self.__log.debug("_pkg_name=%s", self._pkg_name)

        self._settings_files = [
            os.path.expandvars(
                os.path.expanduser(
                    f"{p}/{self._pkg_name}.{self.SETTINGS_EXT}"
                )
            )
            for p in self.SETTINGS_PATH
        ]
        self.__log.debug("_settings_files=%s", self._settings_files)

        self._conf = self.load(self._settings_files)

    @property
    def pkg_name(self):
        return self._pkg_name

    @property
    def conf(self):
        return self._conf

    def load(
        self,
        settings_files: list[str] | None = None,
        pkg_name: str | None = None,
    ):
        """Load configuration."""
        if not settings_files:
            settings_files = self._settings_files

        if not pkg_name:
            pkg_name = self._pkg_name

        self.__log.debug(
            "settings_files=%s, pkg_name=%s", settings_files, pkg_name
        )

        try:
            self._conf = Dynaconf(settings_files=settings_files).get(
                self._pkg_name
            )
            return self.conf

        # except TOMLDecodeError as e:
        except Exception as e:
            self.__log.error("%s: configuration is not loaded.", errmsg(e))
            return None

    def to_dict(self):
        """To dict."""
        if self.conf:
            return self.conf.to_dict()
        return None
