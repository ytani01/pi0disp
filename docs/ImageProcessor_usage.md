# `ImageProcessor` ユーティリティクラス

## 概要

`ImageProcessor`は、ディスプレイに画像を表示する前の一般的な前処理タスクを簡単に行うためのヘルパークラスです。

`pi0disp`ライブラリはPIL (Pillow) の`Image`オブジェクトを受け取りますが、多くの場合、手元にある画像はディスプレイのサイズやアスペクト比と一致しません。`ImageProcessor`は、こうした画像をディスプレイに最適化された形式へ変換する処理をカプセル化し、コードを簡潔に保つのに役立ちます。

## 主な使いどころ

1.  **画像のサイズとアスペクト比の調整**
    - 写真やアイコンなど、ディスプレイの解像度と異なるサイズの画像を、アスペクト比を維持したままリサイズして表示したい場合。
    - 画像を画面全体に引き伸ばすのではなく、黒帯を追加（レターボックス化）するか、はみ出した部分を切り取って（クロップ）表示したい場合。

2.  **ガンマ補正（明るさの調整）**
    - 特定のディスプレイで画像が暗すぎたり、明るすぎたりして見える場合に、見た目を補正したい場合。

## 使い方

### 1. インポート

`pi0disp`パッケージから`ImageProcessor`をインポートします。

```python
from pi0disp import ImageProcessor
from PIL import Image
```

### 2. インスタンス化

`ImageProcessor`のインスタンスを作成します。

```python
processor = ImageProcessor()
```

### 3. メソッドの詳細

#### `resize_with_aspect_ratio()`

アスペクト比を維持したまま画像をリサイズし、指定された解像度のキャンバスに配置します。

**パラメータ:**

-   `img` (`Image.Image`): リサイズする元のPIL画像。
-   `target_width` (`int`): ターゲットとなるキャンバスの幅。
-   `target_height` (`int`): ターゲットとなるキャンバスの高さ。
-   `fit_mode` (`str`): フィットモードを選択します。
    -   `"contain"` (デフォルト): 元画像の縦横比を保ったまま、指定した領域に**収まるように**リサイズします。余白は黒で塗りつぶされます（レターボックス形式）。
    -   `"cover"`: 元画像の縦横比を保ったまま、指定した領域を**完全に覆うように**リサイズします。画像の一部が領域からはみ出す場合は中央を基準にクロップされます。

**戻り値:**

-   `Image.Image`: 処理後の新しいPIL画像。

**コード例:**

```python
from pi0disp import ST7789V, ImageProcessor
from PIL import Image

# 画像ファイルを開く
try:
    source_image = Image.open("my_photo.jpg")
except FileNotFoundError:
    print("エラー: 'my_photo.jpg' が見つかりません。")
    exit()

processor = ImageProcessor()

with ST7789V() as lcd:
    # 'contain' モードでリサイズ（黒帯が追加される可能性がある）
    contained_image = processor.resize_with_aspect_ratio(
        source_image,
        lcd.width,

lcd.height,
        fit_mode="contain"
    )
    lcd.display(contained_image)
    
    # 'cover' モードでリサイズ（画像の一部がクロップされる可能性がある）
    # covered_image = processor.resize_with_aspect_ratio(
    #     source_image,
    #     lcd.width,
    #     lcd.height,
    #     fit_mode="cover"
    # )
    # lcd.display(covered_image)
```

#### `apply_gamma()`

画像にガンマ補正を適用します。

**パラメータ:**

-   `img` (`Image.Image`): 補正対象のPIL画像。
-   `gamma` (`float`): ガンマ値。
    -   `1.0`: 変化なし。
    -   `> 1.0`: 画像が暗くなります。
    -   `< 1.0`: 画像が明るくなります。一般的に`2.2`が標準的なモニタの逆補正値として使われます。

**戻り値:**

-   `Image.Image`: 処理後の新しいPIL画像。

**コード例:**

```python
# ... 前の例の続き ...

# 画像を少し明るくする
bright_image = processor.apply_gamma(contained_image, gamma=0.8)

lcd.display(bright_image)
```

## 総合的なサンプルコード

デジタルフォトフレームのように、画像を読み込んで画面に最適化して表示する一連の流れです。

完全なサンプルコードは、以下のファイルを参照してください。

[samples/image_processor_example.py](../samples/image_processor_example.py)

