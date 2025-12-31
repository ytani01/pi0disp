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

### `[pi0disp.spi]` セクション (ハードウェア接続設定)

| 項目名 | 説明 | デフォルト値 |
| :--- | :--- | :--- |
| `cs` | SPI Chip Select ピン (GPIO番号) | 8 |
| `rst` | Reset ピン (GPIO番号) | 25 |
| `dc` | Data/Command ピン (GPIO番号) | 24 |
| `bl` | バックライト制御ピン (GPIO番号) | 23 |
| `channel` | SPI チャンネル (0 または 1) | 0 |
| `speed_hz` | SPI 通信クロック周波数 (Hz) | 40000000 |

---

## 最適な設定の確認 (`lcd_check.py`)

使用しているパネルに最適な `invert` と `rgb` 設定を一目で確認するためのツールです。

```bash
uv run samples/lcd_check.py
```

画面の指示に従って、背景が漆黒になり、色が正しく見える設定を `pi0disp.toml` に記入してください。

---

## クイックスタート (図形とテキストの描画)

以下のサンプルは、ディスプレイを初期化し、図形やテキストを描画して5秒間表示する最もシンプルなプログラムです。

```python
import time
from PIL import Image, ImageDraw, ImageFont
from pi0disp.disp.st7789v import ST7789V

# 1. 初期化 (pi0disp.toml の設定が自動適用されます)
disp = ST7789V(rotation=90)

# 2. キャンバスの作成
img = Image.new("RGB", (disp.size.width, disp.size.height), "black")
draw = ImageDraw.Draw(img)

# 3. 図形の描画 (四角、円、線)
draw.rectangle([20, 20, 120, 120], outline="yellow", width=3)
draw.ellipse([180, 30, 280, 130], fill="red")
draw.line([0, disp.size.height-1, disp.size.width-1, 0], fill="green")

# 4. テキストの描画 (大きなフォント)
try:
    font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 40)
except:
    font = ImageFont.load_default()
draw.text((80, 150), "pi0disp", fill="cyan", font=font)

# 5. 表示と待機
disp.display(img)
time.sleep(5)  # 5秒間表示を維持

# 6. 終了処理
disp.close()
```

---

## 主要メソッド

#### `display(image: Image.Image)`
画面全体に PIL Image を表示します。内部で RGB565 への高速変換が行われます。

#### `display_region(image: Image.Image, x0, y0, x1, y1)`
指定した矩形領域のみを更新します。アニメーションや部分更新に有効です。

#### `set_rotation(rotation: int)`
表示方向を変更します (0, 90, 180, 270)。

#### `set_brightness(brightness: int)`
バックライトの明るさを 0-255 で変更します。

#### `close()`
ディスプレイをスリープさせ、リソースを解放します。
