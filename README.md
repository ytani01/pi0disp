# pi0disp - Raspberry Pi用 ST7789V 高速ディスプレイドライバ

## 概要

`pi0disp`は、Raspberry Pi（特にRaspberry Pi Zero 2Wのようなリソースに制約のあるモデル）でST7789V搭載ディスプレイを効率的に駆動するために設計された、Python製の**高速ディスプレイドライバライブラリ**です。

`pigpio`ライブラリを利用したSPI通信をベースに、ダーティリージョン（画面の変更があった領域のみ）の更新、メモリプール、適応的なデータ転送チャンクサイズの調整といった高度な最適化技術を実装しており、CPU負荷を抑えながら高いフレームレートを実現します。

また、基本的な動作確認やパフォーマンス測定のためのシンプルな**CLIツール**も同梱しています。

## 特徴

- **高速な描画パフォーマンス**: 変更があった画面領域のみを転送することで、SPI通信量を最小限に抑え、アニメーションなどを滑らかに表示します。
- **モジュラーな最適化コア**: `performance_core.py`に実装された汎用的な最適化機能（メモリプール、領域最適化、パフォーマンスモニタなど）により、高いパフォーマンスと拡張性を両立しています。
- **シンプルなCLI**: `click`ライブラリをベースにした直感的なコマンドラインインターフェースを提供し、ディスプレイのテストや制御を簡単に行えます。
- **柔軟な設定**: SPI通信速度、ターゲットFPS、アニメーションのパラメータなどをコマンドラインオプションで柔軟に指定できます。
- **電源管理**: ディスプレイのON/OFFやスリープモードへの移行をサポートします。

## 要件

### ハードウェア

- Raspberry Pi (全モデルをサポート)
- ST7789V搭載 SPIディスプレイ

### ソフトウェア

- Python 3.11 以降
- `pigpio` デーモン (インストールと実行が必要です)

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

2.  Pythonの仮想環境を作成し、有効化します。（推奨）
    ```sh
    python -m venv .venv
    source .venv/bin/activate
    ```

3.  依存パッケージをインストールします。
    ```sh
    pip install -e .
    ```
    開発用の依存関係を含める場合は、以下のようにインストールしてください。
    ```sh
    pip install -e ".[dev]"
    ```

## 使い方

### ライブラリとしての利用

`pi0disp`のコア機能は `ST7789V` クラスです。Pythonスクリプトから直接インポートして使用できます。

以下のコード例は [`samples/basic_usage.py`](./samples/basic_usage.py) としても保存されており、実際に実行して動作を確認できます。

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

### CLIツール (動作デモ)

インストール後、`pi0disp`コマンドで動作確認用のツールを利用できます。

#### ヘルプの表示

```sh
pi0disp --help
```

#### パフォーマンスデモの実行

バウンドするボールのアニメーションデモを実行し、描画パフォーマンスを測定します。これはドライバの差分描画機能のデモンストレーションです。

```sh
pi0disp test
```

**オプション例:**

-   ターゲットFPSを60に、ボールの数を5に設定:
    ```sh
    pi0disp test --fps 60 --num-balls 5
    ```
-   SPI通信速度を40MHzに設定:
    ```sh
    pi0disp test --speed 40000000
    ```

デモは `Ctrl+C` で終了します。

#### ディスプレイをオフにする

ディスプレイをスリープモードに移行させ、バックライトを消灯します。

```sh
pi0disp off
```

## プロジェクト構成

-   `src/pi0disp/__main__.py`: `click`を使用したCLIのエントリーポイント。
-   `src/pi0disp/commands/`: `test`や`off`などの各サブコマンドの実装。
-   `src/pi0disp/st7789v.py`: ST7789Vディスプレイのハードウェアを直接制御するコア・ドライバクラス。
-   `src/pi0disp/performance_core.py`: メモリ管理、領域最適化、パフォーマンス監視など、性能向上に関わる汎用的な機能を提供するモジュール。
-   `src/pi0disp/utils.py`: `performance_core`の機能をラップし、画像変換などの高レベルなユーティリティ関数を提供するモジュール。

## ライセンス

このプロジェクトは [MITライセンス](LICENSE) の下で公開されています。

## 作者

-   Yoichi Tanibayashi (yoichi@tanibayashi.jp)