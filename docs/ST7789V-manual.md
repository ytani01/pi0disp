# ST7789V ドライバマニュアル

## 概要

このマニュアルは、Raspberry Pi 用 ST7789V ディスプレイドライバ (`pi0disp.ST7789V`) の使用方法と機能について、初級プログラマ向けに簡潔に説明します。

## クラスリファレンス

### `ST7789V` クラス

`ST7789V`ディスプレイドライバのコンストラクタです。

```python
__init__(
    self,
    bl_at_close: bool = False,
    pin: SpiPins | None = None,
    brightness: int = 255,
    channel: int = 0,
    speed_hz: int | None = None,
    size: DispSize | None = None,
    rotation: int | None = None,
    x_offset: int | None = None,
    y_offset: int | None = None,
    invert: bool = True,
    bgr: bool = True,
    debug=False,
)
```

**パラメータ:**

- `bl_at_close` (`bool`): `close()`メソッド呼び出し時にバックライトをオフにするかどうか。
- `pin` (`SpiPins | None`): SPIピン構成 (RST, DC, CS, BLのGPIO番号)。指定しない場合、設定ファイルまたはデフォルト値を使用します。
- `brightness` (`int`): 初期バックライトの明るさ (0-255)。
- `channel` (`int`): pigpioによって使用されるSPIチャンネル (0または1)。
- `speed_hz` (`int | None`): SPI通信速度 (Hz)。指定しない場合、設定ファイルまたはデフォルト値を使用します。
- `size` (`DispSize | None`): ディスプレイの物理サイズ (幅, 高さ)。
- `rotation` (`int | None`): ディスプレイの初期回転角度 (0, 90, 180, 270)。
- `x_offset` (`int | None`): カラムアドレスのオフセット。画面端にゴミが出る場合や更新されない場合に設定します。
- `y_offset` (`int | None`): 行アドレスのオフセット。
- `invert` (`bool`): ディスプレイの色を反転するかどうか。`True`で反転を有効にします。
- `bgr` (`bool`): BGRカラー順序を使用するかどうか。`True`でBGR、`False`でRGB。
- `debug` (`bool`): デバッグモードを有効にするか。

### 関連クラスと型

### `DispSize`

ディスプレイの幅と高さを表す名前付きタプルです。

```python
DispSize(width: int, height: int)
```

**属性:**

- `width` (`int`): ディスプレイの幅（ピクセル単位）。
- `height` (`int`): ディスプレイの高さ（ピクセル単位）。

### `SpiPins`

SPI通信に使用するピン構成を表す名前付きタプルです。

```python
SpiPins(rst: int, dc: int, cs: Optional[int] = None, bl: Optional[int] = None)
```

**属性:**

- `rst` (`int`): リセットピンのGPIO番号。
- `dc` (`int`): データ/コマンド選択ピンのGPIO番号。
- `cs` (`Optional[int]`): チップセレクトピンのGPIO番号。オプション。
- `bl` (`Optional[int]`): バックライト制御ピンのGPIO番号。オプション。
## メソッドリファレンス

### `init_display()`

ST7789Vのハードウェア初期化シーケンスを実行します。ディスプレイの電源投入、カラーモード設定、表示オンなどを行います。

```python
init_display(self)
```

### `set_rotation(rotation: int)`

ディスプレイの回転を設定します。回転角度に応じてMADCTLレジスタを更新し、表示方向とカラー順序を制御します。

```python
set_rotation(self, rotation: int)
```

**パラメータ:**

- `rotation` (`int`): 回転角度 (0, 90, 180, 270)。

### `write_pixels(pixel_bytes: bytes)`

現在のウィンドウにピクセルデータの生バッファを書き込みます。データは `set_window` で設定された領域に書き込まれます。

```python
write_pixels(self, pixel_bytes: bytes)
```

**パラメータ:**

- `pixel_bytes` (`bytes`): 書き込むピクセルデータ (RGB565フォーマット)。

### `display(image: Image.Image)`

画面全体にPIL Imageオブジェクトを表示します。

```python
display(self, image: Image.Image)
```

**パラメータ:**

- `image` (`Image.Image`): 表示するPIL Imageオブジェクト。

### `display_region(image: Image.Image, x0: int, y0: int, x1: int, y1: int)`

指定された領域内にPIL Imageオブジェクトの一部を表示します。

```python
display_region(self, image: Image.Image, x0: int, y0: int, x1: int, y1: int)
```

**パラメータ:**

- `image` (`Image.Image`): 表示するPIL Imageオブジェクト。
- `x0` (`int`): 描画領域の左上X座標。
- `y0` (`int`): 描画領域の左上Y座標。
- `x1` (`int`): 描画領域の右下X座標。
- `y1` (`int`): 描画領域の右下Y座標。
### `close(bl_switch: bool | None = None)`

リソースをクリーンアップし、ディスプレイをスリープ状態にします。SPI接続を閉じ、DISPOFF/SLPINコマンドを送信します。

```python
close(self, bl_switch: bool | None = None)
```

**パラメータ:**

- `bl_switch` (`bool | None`): バックライトの最終状態を明示的に指定します。`None`の場合、オブジェクト生成時の`bl_at_close`設定に従います。

### `dispoff()`

ディスプレイをオフにします (DISPOFFコマンド)。バックライトもオフにします。

```python
dispoff(self)
```

### `sleep()`

ディスプレイをスリープモードにします (SLPINコマンド)。バックライトもオフにします。

```python
sleep(self)
```

### `wake()`

ディスプレイをスリープモードから起動します (SLPOUTコマンド)。バックライトもオンにします。

```python
wake(self)
```

## パラメータリファレンス

### `ST7789V.CMD`

ST7789Vコントローラが認識するコマンドコードの辞書です。

| コマンド | 値 (Hex) | 説明 |
|----------|----------|------|
| `SWRESET`  | `0x01`     | ソフトウェアリセット |
| `SLPIN`    | `0x10`     | スリープモードオン |
| `SLPOUT`   | `0x11`     | スリープモードオフ |
| `NORON`    | `0x13`     | ノーマルディスプレイオン |
| `INVOFF`   | `0x20`     | ディスプレイ反転オフ |
| `INVON`    | `0x21`     | ディスプレイ反転オン |
| `DISPOFF`  | `0x28`     | ディスプレイオフ |
| `DISPON`   | `0x29`     | ディスプレイオン |
| `CASET`    | `0x2A`     | カラムアドレスセット |
| `RASET`    | `0x2B`     | 行アドレスセット |
| `RAMWR`    | `0x2C`     | RAMへ書き込み |
| `MADCTL`   | `0x36`     | メモリデータアクセス制御 |
| `COLMOD`   | `0x3A`     | インターフェースピクセルフォーマット |

## 使用例

以下は、`ST7789V`ドライバを使用してディスプレイを初期化し、画像を表示し、様々なオプションを試す簡単な例です。

```python
import time
from PIL import Image
from pi0disp import ST7789V, DispSize, SpiPins

# 1. ディスプレイの初期化
# デフォルト設定 (invert=True, bgr=True) で初期化
# 実際のピン番号に合わせてSpiPinsを設定してください
# 例: pin = SpiPins(rst=25, dc=24, bl=23)
# size = DispSize(width=240, height=320)
try:
    with ST7789V(
        # pin=SpiPins(rst=25, dc=24, bl=23), # 必要に応じてコメントを外して設定
        # size=DispSize(width=240, height=320), # 必要に応じてコメントを外して設定
        invert=True,
        bgr=True,
        debug=False
    ) as lcd:
        print("ディスプレイ初期化完了")

        # 2. 赤い画面を表示
        print("赤い画面を表示します (5秒間)")
        red_image = Image.new("RGB", lcd.size, "red")
        lcd.display(red_image)
        time.sleep(5)

        # 3. 緑の画面を表示し、回転 (90度)
        print("緑の画面を表示し、90度回転します (5秒間)")
        green_image = Image.new("RGB", lcd.size, "green")
        lcd.set_rotation(90) # 回転を設定
        lcd.display(green_image)
        time.sleep(5)

        # 4. 青い画面を表示し、バックライトを制御
        print("青い画面を表示し、バックライトを50%に設定します (5秒間)")
        blue_image = Image.new("RGB", lcd.size, "blue")
        lcd.set_rotation(0) # 回転を元に戻す
        lcd.set_brightness(128) # バックライトを50%の明るさに
        lcd.display(blue_image)
        time.sleep(5)
        lcd.set_brightness(255) # バックライトを元の明るさに戻す

        # 5. invert=False (反転なし) でテスト
        # 一旦閉じて、新しい設定で再初期化
        lcd.close() # 既存のLCDインスタンスを閉じる
        with ST7789V(invert=False, bgr=True) as lcd_no_invert:
            print("反転なしで赤い画面を表示します (5秒間)")
            red_image_no_invert = Image.new("RGB", lcd_no_invert.size, "red")
            lcd_no_invert.display(red_image_no_invert)
            time.sleep(5)

        # 6. bgr=False (RGB順) でテスト
        # 一旦閉じて、新しい設定で再初期化
        # lcd_no_invert.close() # 既に閉じてるので不要
        with ST7789V(invert=True, bgr=False) as lcd_rgb_order:
            print("RGB順で赤い画面を表示します (5秒間)")
            red_image_rgb_order = Image.new("RGB", lcd_rgb_order.size, "red")
            lcd_rgb_order.display(red_image_rgb_order)
            time.sleep(5)

        print("テスト終了。")

except RuntimeError as e:
    print(f"エラー: {e}")
except KeyboardInterrupt:
    print("スクリプトがユーザーによって中断されました。")
```
