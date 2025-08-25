# pi0disp - Raspberry Pi用 ST7789V 高速ディスプレイドライバ

## 概要

`pi0disp`は、
Raspberry Pi
(特にRaspberry Pi Zero 2Wのようなリソースに制約のあるモデル)で
ST7789V搭載ディスプレイを効率的に駆動するために設計された、
Python製の**高速ディスプレイドライバライブラリ**です。

`pigpio`ライブラリを利用したSPI通信をベースに、
ダーティリージョン(画面の変更があった領域のみ)の更新、
メモリプール、
適応的なデータ転送チャンクサイズの調整
といった高度な最適化技術を実装しており、
CPU負荷を抑えながら高いフレームレートを実現します。

また、
基本的な動作確認やパフォーマンス測定のための
シンプルな**CLIツール**も同梱しています。


## 特徴

- **高速な描画パフォーマンス**: `pigpio`, `numpy`を活用し、高速・軽量になるよう実装しています。
- **最適化ライブラリ**: `performance_core.py`に実装された汎用的な最適化機能(メモリプール、領域最適化、パフォーマンスモニタなど)により、高いパフォーマンスと拡張性を両立しています。


## 要件

### ハードウェア

- Raspberry Pi
- ST7789V搭載 SPIディスプレイ


### ソフトウェア

- Python 3.11 以降
- `pigpio`: ライブラリ、デーモン

```sh
# pigpioのインストール
sudo apt update
sudo apt install pigpio

# pigpioデーモンの起動
sudo systemctl start pigpiod
```

## インストール

1.  リポジトリをクローンします。
    ```sh
    git clone <repository_url>
    cd pi0disp
    ```

2.  Pythonの仮想環境を作成
    ※ 有効化()は不要！

    ```sh
    python -m venv .venv
    ```

3.  依存パッケージをインストールします。

    ```sh
    pip install -e .
    ```

    開発用の依存関係を含める場合は、以下のようにインストールしてください。
    ```sh
    pip install -e . --group dev
    ```


## 使い方

### ライブラリとしての利用

`pi0disp`のコア機能は `ST7789V` クラスです。
Pythonスクリプトから直接インポートして使用できます。

以下のコード例は [`samples/basic_usage.py`](./samples/basic_usage.py) としても保存されており、実際に実行して動作を確認できます。

``` sh
uv run samples/basic_usage.py
```

**基本的な使用例:**

```python
from pi0disp import ST7789V
from PIL import Image, ImageDraw

# ディスプレイを初期化
with ST7789V() as lcd:
    # PILを使って画像を作成
    image = Image.new("RGB", (lcd.width, lcd.height), "black")
    draw = ImageDraw.Draw(image)

    # 円を描画
    draw.ellipse(
        (10, 10, lcd.width - 10, lcd.height - 10),
        fill="blue",
        outline="white"
    )

    # ディスプレイに表示
    lcd.display(image)
```

**部分更新（差分描画）:**

変更があった領域のみを転送することで、より高いパフォーマンスを実現できます。

```python
    # ... (上記のコードに続けて)

    # 画像の一部を変更
    draw.rectangle((50, 50, 100, 100), fill="red")

    # 変更された領域のみをディスプレイに転送
    lcd.display_region(image, 50, 50, 100, 100)
```

### CLIツール (動作確認用)

インストール後、`pi0disp`コマンドで動作確認用のツールを利用できます。

#### ヘルプの表示

```sh
uv run pi0disp --help
```

#### パフォーマンスデモ: `ball_anime`

バウンドするボールのアニメーションデモを実行し、描画パフォーマンスを測定します。これはドライバの差分描画機能のデモンストレーションです。

```sh
uv run pi0disp ball_anime
```

**オプション例:**

-   ターゲットFPSを60に、ボールの数を5に設定:
    ```sh
    uv run pi0disp ball_anime --fps 60 --num-balls 5
    ```
-   SPI通信速度を40MHzに設定:
    ```sh
    uv run pi0disp test --speed 40000000
    ```

デモは `Ctrl+C` で終了します。

#### ディスプレイをオフにする

ディスプレイをスリープモードに移行させ、バックライトを消灯します。

```sh
uv run pi0disp off
```


## ライセンス

このプロジェクトは [MITライセンス](LICENSE) の下で公開されています。
