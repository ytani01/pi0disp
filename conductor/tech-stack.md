# Tech Stack

## プログラミング言語
*   Python (>= 3.13)

## 主要ライブラリ/フレームワーク
*   **cairo (pycairo)**: 高品質なベクトルグラフィックス描画用
*   **cairosvg**: SVG画像処理用
*   **click**: CLIツール構築用
*   **dynaconf**: 設定管理（読み込み）用
*   **tomlkit**: 設定ファイルの対話型更新・保存用（コメント維持）
*   **numpy**: 高速な数値計算、特に画像処理の一部で使用
*   **pigpio**: Raspberry Pi の GPIO 制御および高速SPI通信用
*   **psutil**: システムの CPU 使用率やプロセス情報の取得（ベンチマーク用）
*   **pillow**: 画像処理用 (PIL のフォーク)

## 開発ツール/依存関係
*   **flake8**: コードのリント
*   **isort**: インポートのソート
*   **mypy**: 静的型チェック
*   **pytest**: テストフレームワーク
*   **pytest-cov**: カバレッジ測定
*   **pytest-xdist**: 並列テスト実行
*   **ruff**: 高速なPythonリンターおよびフォーマッター

## 実行環境
*   Raspberry Pi (GPIO, SPI, pigpiod デーモン)
