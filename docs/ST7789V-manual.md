# ST7789V ディスプレイドライバ リファレンスマニュアル

`pi0disp` ライブラリに含まれる `ST7789V` クラスは、Raspberry Pi 用に最適化された高速なディスプレイドライバです。

## クラス: `ST7789V`

`DispSpi` を継承し、ST7789V コントローラ特有の初期化と描画最適化を提供します。

### インポート

```python
from pi0disp.disp.st7789v import ST7789V
from pi0disp.disp.disp_base import DispSize
```

### コンストラクタ: `__init__(...)`

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
    bgr: bool = False,
    debug=False,
)
```

**パラメータ:**

*   `bl_at_close` (bool): `close()` 時にバックライトを消灯するか。 (デフォルト: `False`)
*   `pin` (SpiPins | None): SPIピン構成。省略時は `pi0disp.toml` の設定を使用。
*   `brightness` (int): バックライト輝度 (0-255)。 (デフォルト: `255`)
*   `channel` (int): SPI チャンネル (0 または 1)。 (デフォルト: `0`)
*   `speed_hz` (int | None): SPI 通信速度。 (デフォルト: `40,000,000`)
*   `size` (DispSize | None): 物理サイズ。 (デフォルト: `240x320`)
*   `rotation` (int | None): 回転角度 (0, 90, 180, 270)。 (デフォルト: `0`)
*   `x_offset`, `y_offset` (int | None): カラム/行の表示オフセット。 (デフォルト: `0`)
*   `invert` (bool): 色反転設定。通常、黒背景パネルでは `True`。 (デフォルト: `True`)
*   `bgr` (bool): BGRカラー順序を使用するか。 `False` で標準の RGB。 (デフォルト: `False`)
*   `debug` (bool): デバッグログを出力するか。

---

### 主要メソッド

#### `display(image: Image.Image)`
画面全体に PIL Image を表示します。内部で RGB565 への高速変換が行われます。

#### `display_region(image: Image.Image, x0, y0, x1, y1)`
指定した矩形領域のみを更新します。アニメーションや部分更新に有効です。

#### `set_rotation(rotation: int)`
表示方向を変更します。
*   `ST7789V.NORTH` (0): 縦向き (240x320)
*   `ST7789V.EAST` (90): 横向き (320x240)
*   `ST7789V.SOUTH` (180): 縦向き・逆 (240x320)
*   `ST7789V.WEST` (270): 横向き・逆 (320x240)

#### `set_brightness(brightness: int)`
バックライトの明るさを 0-255 で変更します。

#### `close()`
ディスプレイをスリープさせ、リソースを解放します。

---

## クイックスタート (Hello World)

```python
from PIL import Image, ImageDraw
from pi0disp.disp.st7789v import ST7789V

# 初期化 (標準設定)
disp = ST7789V(rotation=90)

# 画像の作成 (320x240)
img = Image.new("RGB", (disp.size.width, disp.size.height), "blue")
draw = ImageDraw.Draw(img)
draw.text((10, 10), "Hello World!", fill="white")

# 表示
disp.display(img)

# 終了処理
input("Press Enter to exit...")
disp.close()
```

## トラブルシューティング

*   **色が正しくない (赤と青が逆):** `bgr` パラメータを反転させてください。
*   **色が反転している (黒が白に見える):** `invert` パラメータを変更してください。
*   **表示位置がずれている:** `x_offset` や `y_offset` を調整してください。
