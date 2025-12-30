#
# (c) 2025 Yoichi Tanibayashi
#
import time
from typing import NamedTuple, Optional, Union

import pigpio

from ..utils.mylogger import errmsg
from .disp_base import DispBase, DispSize


class SpiPins(NamedTuple):
    """
    SPI通信に使用するピン構成を表すクラス。

    属性:
        rst (int): リセットピンのGPIO番号。
        dc (int): データ/コマンド選択ピンのGPIO番号。
        cs (Optional[int]): チップセレクトピンのGPIO番号。オプション。
        bl (Optional[int]): バックライト制御ピンのGPIO番号。オプション。
    """

    rst: int
    dc: int
    cs: Optional[int] = None
    bl: Optional[int] = None


class DispSpi(DispBase):
    """
    SPI通信を介してディスプレイを制御するクラス。
    DispBaseを継承し、SPI固有の初期化、データ転送、ピン制御を実装する。
    """

    # DEF_PIN = SpiPins(rst=25, dc=24, bl=23)
    DEF_PIN_DICT = {"rst": 25, "dc": 24, "bl": 23, "cs": 8}
    SPEED_HZ = {
        "default": 8_000_000,
        "max": 32_000_000,
    }

    def __init__(
        self,
        bl_at_close: bool = False,
        pin: SpiPins | None = None,
        brightness: int = 255,
        channel: int = 0,
        speed_hz: int | None = None,
        *,
        size: DispSize | None = None,
        rotation: int | None = None,
        debug=False,
    ):
        """
        SPIディスプレイドライバを初期化する。

        SPIバスとGPIOピンを設定し、pigpioへの接続を行う。
        以前のプロセスによって残された可能性のあるSPIハンドルをクリーンアップするロジックも含む。

        パラメータ:
            bl_at_close (bool): `close()`メソッドが呼び出されたときにバックライトをオフにするかどうか。
            pin (SpiPins | None): SPIピン構成 (RST, DC, CS, BLのGPIO番号)。
                                  指定しない場合、設定ファイルまたはデフォルト値を使用。
            brightness (int): 初期バックライトの明るさ (0-255)。
            channel (int): pigpioによって使用されるSPIチャンネル (0または1)。
            speed_hz (int | None): SPI通信速度 (Hz)。
                                   指定しない場合、設定ファイルまたはデフォルト値 (8MHz) を使用。
            size (DispSize | None): ディスプレイの物理サイズ (幅, 高さ)。
            rotation (int | None): ディスプレイの初期回転角度。
            debug (bool): デバッグモードを有効にするか。
        """
        super().__init__(size, rotation, debug=debug)
        self.__debug = debug

        # Add a workaround for unclean shutdowns (e.g., after kill -9).
        # This iterates through all possible SPI handles and attempts to close them,
        # cleaning up any stale handles left over from the previous process.
        self._log.debug(
            "残存する可能性のあるSPIハンドルをクリーンアップします。"
        )
        for h in range(32):
            try:
                self.pi.spi_close(h)
            except pigpio.error:
                pass

        self._log.debug(
            "bl_at_close=%s, brightness=%s", bl_at_close, brightness
        )
        self._log.debug("SPI: channel=%s,speed_hz=%s", channel, speed_hz)
        self._log.debug("GPIO: pin=%s", pin)

        self.bl_at_close = bl_at_close

        if pin is None:
            pd = self.DEF_PIN_DICT.copy()
            for k in ["rst", "dc", "bl", "cs"]:
                if self._conf.data.get("spi").get(k):
                    pd[k] = self._conf.data.spi.get(k)
            pin = SpiPins(
                rst=pd["rst"], dc=pd["dc"], bl=pd["bl"], cs=pd["cs"]
            )
            self._log.debug("GPIO: pin=%s", pin)
        self.pin = pin

        if speed_hz is None:
            speed_hz = self.conf.data.spi.get("speed_hz")
            if speed_hz:
                self._log.debug("speed_hz=%s (設定ファイル)", speed_hz)
            else:
                speed_hz = self.SPEED_HZ["default"]
                self._log.debug("speed_hz=%s (デフォルト)", speed_hz)

        self._brightness = brightness
        self._backlight_on = False

        # Configure GPIO pins
        for p in [self.pin.rst, self.pin.dc, self.pin.bl, self.pin.cs]:
            if p:
                self.pi.set_mode(p, pigpio.OUTPUT)

        # Open SPI handle
        # SPI handle options:
        #   if CS is controlled by pigpio, channel is usually used.
        self.spi_handle = self.pi.spi_open(channel, speed_hz, 0)
        if self.spi_handle < 0:
            raise RuntimeError(
                f"SPIバスを開けませんでした: handle={self.spi_handle}"
            )

    # def __enter__(self):
    #     self._log.debug("")
    #     return self

    # def __exit__(self, exc_type, exc_val, exc_tb):
    #     self._log.debug(
    #         "exc_type=%s,exc_val=%s,exc_tb=%s", exc_type, exc_val, exc_tb
    #     )
    #     self.close()

    def _write_command(self, command: int):
        """
        ディスプレイにコマンドバイトを送信する。

        パラメータ:
            command (int): 送信するコマンドバイト (0x00-0xFF)。
        """
        self.pi.write(self.pin.dc, 0)  # D/CピンをLowに設定（コマンドモード）
        self.pi.spi_write(self.spi_handle, [command])

    def _write_data(self, data: Union[int, bytes, list]):
        """
        ディスプレイにデータバイトまたはバッファを送信する。

        パラメータ:
            data (Union[int, bytes, list]): 送信するデータ。
                                            単一のバイト (int) またはバイトのシーケンス (bytes, list)。
        """
        self.pi.write(self.pin.dc, 1)  # D/CピンをHighに設定（データモード）
        if isinstance(data, int):
            self.pi.spi_write(self.spi_handle, [data])
        else:
            self.pi.spi_write(self.spi_handle, data)

    def set_brightness(self, brightness: int):
        """
        バックライトの明るさを設定する (0-255)。

        `set_backlight()`がオンの場合にのみ適用される。

        パラメータ:
            brightness (int): 明るさの値 (0-255)。
        """
        if not self.pin.bl:
            self._log.debug("pin.bl=%s: 何もしません。", self.pin.bl)
            return

        # self.set_backlightのON/OFFに関わらず、値を保持する。
        self._brightness = max(0, min(255, brightness))

        if self._backlight_on:
            self.pi.set_PWM_dutycycle(self.pin.bl, self._brightness)

    def set_backlight(self, on: bool):
        """
        バックライトをオンまたはオフにする。

        設定された明るさの値は維持される。

        パラメータ:
            on (bool): `True`でオン、`False`でオフ。
        """
        if not self.pin.bl:
            self._log.debug("pin.bl=%s: 何もしません。", self.pin.bl)
            return

        self._backlight_on = on

        if on:
            self.pi.set_PWM_dutycycle(self.pin.bl, self._brightness)
        else:
            self.pi.set_PWM_dutycycle(self.pin.bl, 0)

    def init_display(self):
        """
        SPIディスプレイの初期化処理を実行する。

        GPIOピンのリセットとバックライトの制御を行う。
        """
        self._log.debug("バックライトON")

        self.set_backlight(True)

        # Hardware reset
        self.pi.write(self.pin.rst, 1)
        time.sleep(0.01)
        self.pi.write(self.pin.rst, 0)
        time.sleep(0.01)
        self.pi.write(self.pin.rst, 1)
        time.sleep(0.5)

    def close(self, bl_switch: bool | None = None):
        """
        リソースをクリーンアップし、SPI接続とGPIOピンを解放する。

        パラメータ:
            bl_switch (bool | None): バックライトの最終状態を明示的に指定する。
                                    `None`の場合、オブジェクト生成時の`bl_at_close`設定に従う。
        """
        self._log.debug("bl_switch=%s", bl_switch)

        if self.pi.connected:
            # SPI handle
            if self.spi_handle >= 0:
                try:
                    self.pi.spi_close(self.spi_handle)
                    self._log.debug(
                        "SPIをクローズ: spi_handle=%s", self.spi_handle
                    )
                except Exception as e:
                    self._log.warning(errmsg(e))

            # backlight
            if self.pin.bl is not None:
                if not bl_switch:
                    bl_switch = self.bl_at_close
                self._log.debug("bl_switch=%s", bl_switch)
                self.set_backlight(bl_switch)
        else:
            self._log.warning(
                "pigpiodに接続していません (%s)。", self.pi.connected
            )

        super().close()  # self.pi の終了処理(stop)は、親クラスに任せる
