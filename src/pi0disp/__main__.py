#
# (c) 2025 Yoichi Tanibayashi
#
import time
import click

from PIL import Image

from . import ST7789V, __version__
from .my_logger import get_logger

log = get_logger(__name__)

@click.group()
@click.version_option(version=__version__)
def cli():
    """
    ST7789V Display Driver CLI
    """
    pass

@cli.command()
@click.option('--speed', default=40000000, type=int, help='SPI speed in Hz')
def test(speed):
    """
    Run a basic display test.
    """
    log.info(f"ST7789V({__version__}) ドライバテスト開始")
    log.info(f"SPI速度: {speed} Hz")

    try:
        with ST7789V(speed_hz=speed) as lcd:
            log.info("初期化成功。新しいdisplay()メソッドで画面を青色で塗りつぶします...")
            
            # 青一色のPIL Imageオブジェクトを作成
            img = Image.new("RGB", (lcd.width, lcd.height), "blue")
                
            # 新しいdisplayメソッドで描画
            lcd.display(img)
                
            time.sleep(3)
            log.info("テスト完了")
    except Exception as e:
        log.error(f"エラーが発生しました: {e}")
        exit(1)

if __name__ == "__main__":
    cli()
