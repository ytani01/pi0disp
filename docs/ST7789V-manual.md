# ST7789V ディスプレイドライバ リファレンスマニュアル

`pi0disp` ライブラリに含まれる `ST7789V` クラスは、Raspberry Pi 用に最適化された高速なディスプレイドライバです。

---

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
    invert: bool | None = None,
    bgr: bool | None = None,
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
*   `invert` (bool | None): 色反転設定。省略時は設定ファイルまたは `True`。
*   `bgr` (bool | None): BGRカラー順序を使用するか。省略時は設定ファイルまたは `False`。
*   `debug` (bool): デバッグログを出力するか。

---

## 設定ファイル: `pi0disp.toml`

プロジェクトのルートディレクトリに `pi0disp.toml` を配置することで、動作を詳細にカスタマイズできます。

### `[pi0disp]` セクション (ディスプレイ基本設定)

| 項目名 | 説明 | デフォルト値 |
| :--- | :--- | :--- |
| `width` | ディスプレイの物理的な幅 (ピクセル) | 240 |
| `height` | ディスプレイの物理的な高さ (ピクセル) | 320 |
| `rotation` | 初回の回転角度 (0, 90, 180, 270) | 0 |
| `x_offset` | 描画開始位置のXオフセット | 0 |
| `y_offset` | 描画開始位置のYオフセット | 0 |
| `invert` | 色反転の有効(`true`)/無効(`false`) | `true` |
| `rgb` | `true`でRGB、`false`でBGR順序を使用 | `true` |

*   **オフセットについて**: 画面の端が欠けたり、ノイズが出る場合は、`x_offset` や `y_offset` を調整してください。
*   **色設定について**: `invert` と `rgb` の正しい組み合わせは、後述の `lcd_check.py` で確認できます。

### `[pi0disp.spi]` セクション (ハードウェア接続設定)

| 項目名 | 説明 | デフォルト値 |
| :--- | :--- | :--- |
| `cs` | SPI Chip Select ピン (GPIO番号) | 8 |
| `rst` | Reset ピン (GPIO番号) | 25 |
| `dc` | Data/Command ピン (GPIO番号) | 24 |
| `bl` | バックライト制御ピン (GPIO番号) | 23 |
| `channel` | SPI チャンネル (0: /dev/spidev0.0, 1: /dev/spidev0.1) | 0 |
| `speed_hz` | SPI 通信クロック周波数 (Hz) | 40000000 |

---

## 最適な設定の確認 (`lcd_check.py`)

使用しているパネルに最適な `invert` と `rgb` 設定を一目で確認するためのツールです。

```bash
uv run samples/lcd_check.py
```

画面に「TEST 1/4」〜「TEST 4/4」が順に表示されます。
1.  **背景が漆黒**（グレーや白っぽくない）
2.  **カラーバーが上から「赤・緑・青」**の順
になっている画面を探し、そこに表示されている `inv` と `bgr` の値をメモしてください。

メモした値に基づき、`pi0disp.toml` を以下のように設定してください。
*   `invert` = (画面の `inv` の値)
*   `rgb` = (画面の `bgr` が `False` なら `true`、`True` なら `false`)

---

## 主要メソッド

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

# 初期化 (pi0disp.toml の設定が自動適用されます)
disp = ST7789V(rotation=90)

# 画像の作成
img = Image.new("RGB", (disp.size.width, disp.size.height), "black")
draw = ImageDraw.Draw(img)
draw.text((20, 20), "Hello ST7789V!", fill="white")

# 表示
disp.display(img)

# 終了処理
input("Press Enter to exit...")
disp.close()
```