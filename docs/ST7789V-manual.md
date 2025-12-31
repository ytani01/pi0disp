# ST7789V ドライバリファレンスマニュアル

## 1. 概要
`pi0disp.ST7789V` は、Raspberry Pi 用に最適化された ST7789V ディスプレイドライバです。`pigpio` ライブラリを使用し、高速な描画（DMA等の最適化を含む）と柔軟な画面回転をサポートします。

## 2. クラスリファレンス

### `ST7789V` クラス
`DispSpi` および `DispBase` を継承した、メインのドライバクラスです。

#### `__init__(...)`
ドライバを初期化し、ディスプレイの制御を開始します。

**シグネチャ:**
```python
def __init__(
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
    debug: bool = False
)
```

**パラメータ:**
- `bl_at_close` (`bool`): `close()` 時にバックライトを消灯するか。デフォルトは `False`。
- `pin` (`SpiPins`): 使用するGPIOピンの構成。`None` の場合は設定ファイル（`pi0disp.toml`）を参照します。
- `brightness` (`int`): 初期バックライト輝度 (0-255)。デフォルトは最大値 `255`。
- `channel` (`int`): SPIチャンネル (0 または 1)。デフォルトは `0`。
- `speed_hz` (`int`): SPI通信速度。デフォルトは 8MHz (`8_000_000`)。
- `size` (`DispSize`): ディスプレイの物理サイズ。デフォルトは `(240, 320)`。
- `rotation` (`int`): 画面の初期向き。以下の定数を使用してください。
- `x_offset`, `y_offset` (`int`): コントローラ内のアドレスオフセット。画面端に余白が出る場合に調整します。
- `invert` (`bool`): 色反転（インバート）の有無。デフォルトは `True`。
- `bgr` (`bool`): 色順序をBGRにするか。`False` の場合はRGBになります。デフォルトは `True`。
- `debug` (`bool`): デバッグログを出力するか。

---

## 3. 定数とプロパティ

### 方向定数 (Rotation Constants)
画面の向きを指定するために使用します。
- `ST7789V.NORTH` (0): 縦持ち（端子が下）
- `ST7789V.EAST` (90): 横持ち（端子が左）
- `ST7789V.SOUTH` (180): 縦持ち（端子が上）
- `ST7789V.WEST` (270): 横持ち（端子が右）

### プロパティ
- `size` (`DispSize`): **現在の回転角に基づいた**論理的な画面サイズ (width, height) を返します。
- `native_size` (`DispSize`): ディスプレイの物理的な（回転していない状態の）サイズを返します。
- `rotation` (`int`): 現在の回転角を取得または設定します。

---

## 4. 主要なメソッド

### `display(image: Image.Image)`
画面全体を更新します。
- **image**: PIL (Pillow) の Image オブジェクト。現在の `size` プロパティと同じサイズである必要があります。

### `set_backlight(value: int | bool)`
バックライトの明るさを調整します。
- **value**: `0-255` の数値、または `True` (255) / `False` (0)。

### `set_rotation(rotation: int)`
実行中に画面の向きを変更します。変更後、`size` プロパティも自動的に更新されます。
- **rotation**: 上述の方向定数を指定します。

### `close()`
リソース（SPI、GPIO）を解放します。`with` 構文を使用してコンテキストマネージャとして利用することを推奨します。

---

## 5. 使用例 (Hello World)

```python
from PIL import Image, ImageDraw
from pi0disp import ST7789V

# コンテキストマネージャによる自動 close()
with ST7789V(rotation=ST7789V.EAST, brightness=128) as lcd:
    # 現在の画面サイズに合わせたキャンバスを作成
    img = Image.new("RGB", lcd.size, "black")
    draw = ImageDraw.Draw(img)

    # 描画の例
    draw.rectangle((0, 0, lcd.size.width-1, lcd.size.height-1), outline="white")
    draw.text((20, 20), "ST7789V Reference", fill="yellow")
    
    # 画面に転送
    lcd.display(img)
```