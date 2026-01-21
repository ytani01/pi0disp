#
# (c) 2025 Yoichi Tanibayashi
#
from abc import ABCMeta
from typing import NamedTuple

import pigpio
from PIL import Image

from ..utils.my_conf import MyConf
from ..utils.mylogger import get_logger


class DispSize(NamedTuple):
    """ディスプレイサイズを表すクラス。"""

    width: int
    height: int


class DispBase(metaclass=ABCMeta):
    # Rotation constants
    NORTH = 0
    EAST = 90
    SOUTH = 180
    WEST = 270
    """
    ディスプレイの抽象基底クラス。
    基本的なディスプレイプロパティとpigpioへの接続管理を扱う。
    """

    DEF_SIZE = DispSize(240, 320)
    DEF_ROTATION = 0

    def __init__(
        self,
        size: DispSize | None = None,
        rotation: int | None = None,
        debug=False,
    ):
        """
        ディスプレイドライバの基底クラスを初期化する。

        設定ファイルからの値、またはデフォルト値を使用してディスプレイのサイズと回転を設定し、
        pigpioデーモンへの接続を確立する。

        パラメータ:
            size (DispSize | None): ディスプレイの物理サイズ (幅, 高さ)。指定しない場合、
                                    設定ファイルまたはデフォルト値 (DEF_SIZE) を使用。
            rotation (int | None): ディスプレイの初期回転角度 (0, 90, 180, 270)。
                                    指定しない場合、設定ファイルまたはデフォルト値 (DEF_ROTATION) を使用。
            debug (bool): デバッグモードを有効にするか。Trueの場合、詳細なログが出力される。
        """
        self.__debug = debug
        self._log = get_logger(self.__class__.__name__, self.__debug)
        self._log.debug("size=%s,rotation=%s", size, rotation)

        # load configuration file
        self._conf = MyConf(debug=self.__debug)

        # size
        if size is None:
            if (
                self._conf.data is not None
                and self._conf.data.get("width")
                and self._conf.data.get("height")
            ):
                size = DispSize(self._conf.data.width, self._conf.data.height)
                self._log.debug("size=%s [conf]", size)
            else:
                size = self.DEF_SIZE
                self._log.debug("size=%s [DEF_SIZE]", size)
        self._native_size = size
        self._size = size

        # rotation
        if rotation is None:
            if self._conf.data is not None and self._conf.data.get(
                "rotation"
            ):
                rotation = self._conf.data.rotation
                self._log.debug("rotation=%s [conf]", rotation)
            else:
                rotation = self.DEF_ROTATION
                self._log.debug("rotation=%s [DEF_ROTATION]", rotation)
        self._rotation = rotation

        # Ensure rotation is int (for basedpyright)
        if rotation is None:
            rotation = self.DEF_ROTATION
        self.rotation = rotation

        # Initialize pigpio
        self.pi = pigpio.pi()
        if not self.pi.connected:
            raise RuntimeError(
                "Could not connect to pigpio daemon. Is it running?"
            )

    def __enter__(self):
        self._log.debug("")
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self._log.debug(
            "exc_type=%s,exc_val=%s,exc_tb=%s", exc_type, exc_val, exc_tb
        )
        self.close()

    @property
    def size(self):
        """現在のディスプレイサイズ (幅, 高さ) を返す。"""
        return self._size

    @property
    def width(self):
        """Width."""
        return self._size.width

    @property
    def height(self):
        """Height."""
        return self._size.height

    @property
    def native_size(self):
        """ディスプレイのネイティブサイズ (回転の影響を受けない物理サイズ) を返す。"""
        return self._native_size

    @property
    def rotation(self):
        """現在のディスプレイ回転角度を返す。"""
        return self._rotation

    @rotation.setter
    def rotation(self, rotation: int):
        """
        ディスプレイの回転角度を設定する。

        回転角度に基づいて、論理的なディスプレイサイズを更新する。
        """
        # self._log.debug("rotation=%s", rotation)

        self._rotation = rotation

        # Swap width and height for portrait/landscape modes
        if rotation in (90, 270):
            self._size = DispSize(
                self._native_size.height, self._native_size.width
            )
        else:
            self._size = self._native_size

        self._log.debug("rotation=%s,size=%s", self._rotation, self.size)

    @property
    def conf(self):
        """設定オブジェクトを返す。"""
        return self._conf

    def init_display(self):
        """
        ディスプレイのハードウェア初期化処理を定義する抽象メソッド。

        継承クラスでオーバーライドされる必要がある。
        """
        self._log.warning("このメソッドはオーバーライドしてください。")

    def display(self, image: Image.Image, full: bool = False):
        """
        画像を表示する抽象メソッド。

        指定されたPIL画像をディスプレイに表示する。
        継承クラスでオーバーライドされる必要がある。

        パラメータ:
            image (Image.Image): 表示するPIL Imageオブジェクト。
            full (bool): 差分更新ではなく全画面を強制的に更新するか。
        """
        if image.size != self._size:
            self._log.debug(
                "画像のサイズをディスプレイに合わせて調整します。"
            )
            image = image.resize(self._size)

    def close(self):
        """
        ディスプレイの接続を閉じ、リソースを解放する。

        pigpioデーモンとの接続を切断する。
        """
        if self.pi.connected:
            self._log.debug("pigpiod接続を閉じます。")
            self.pi.stop()
        else:
            self._log.warning(
                "pigpiodに接続していません (%s)。", self.pi.connected
            )


def get_display_info(debug=False) -> dict:
    """
    設定ファイルからディスプレイ情報を取得する。

    パラメータ:
        debug (bool): デバッグモードを有効にするか。

    戻り値:
        dict: 幅、高さ、回転角度を含む辞書。
    """
    log = get_logger("get_display_info", debug)
    log.debug("設定ファイルを読み込みます。")

    conf = MyConf(debug=debug)
    if conf.data is None:
        log.warning("Configuration data not found.")
        return {"width": None, "height": None, "rotation": None}

    width = conf.data.get("width")
    height = conf.data.get("height")
    rotation = conf.data.get("rotation")
    log.debug("width=%s, height=%s, rotation=%s", width, height, rotation)

    return {"width": width, "height": height, "rotation": rotation}
