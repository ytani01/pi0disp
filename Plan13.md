# Plan 13: Create `tests/test_03_st7789v.py`

`src/pi0disp/disp/st7789v.py` 用のテストプログラム `tests/test_03_st7789v.py` を新規作成します。
これまでのリファクタリングで整えた `pytest` スタイルと `conftest.py` の共通フィクスチャを活用します。

## テスト対象クラス

`pi0disp.disp.st7789v.ST7789V`

## テスト方針

- **`pytest` スタイル**: 関数ベースのテスト、`assert` 文を使用。
- **共通フィクスチャの利用**: `conftest.py` で定義した `mock_pi_constructor`, `mock_logger`, `mock_pi_instance` を使用。
- **追加のモック**:
  - `time.sleep`: 待機時間の短縮のため。
  - `create_optimizer_pack`: `performance_core` のロジックは複雑なため、ユニットテストではモック化して、`ST7789V` のロジックに集中してもよいが、実体が副作用を持たない純粋なロジックであれば実体を使うのもあり。
    - `performance_core` の中身を確認した結果、`MyLogger` 以外は計算ロジック中心であれば実体を使う方針とする（結合テスト寄りになるが、信頼性は高まる）。
    - もし依存が重ければ `patch` する。現状は `create_optimizer_pack` をモック化する方向で検討（呼び出し確認のみにする）。

## テストケース案

1. **初期化 (`__init__`)**
   - 親クラス `DispSpi` の初期化が呼ばれること。
   - `init_display` が呼ばれること。
   - `set_rotation` が呼ばれること。
   - オプティマイザが初期化されること。

2. **ハードウェア初期化 (`init_display`)**
   - ST7789V 固有のコマンドシーケンス (`SWRESET`, `SLPOUT`, `COLMOD`, `DISPON` 等) が送信されること。
   - `time.sleep` が適切に呼ばれること。

3. **回転設定 (`set_rotation`)**
   - `MADCTL` コマンドが適切な値で送信されること (0, 90, 180, 270)。
   - 不正な値で `ValueError` が発生すること。
   - `_last_window` キャッシュがクリアされること。

4. **ウィンドウ設定 (`set_window`)**
   - `CASET`, `RASET`, `RAMWR` コマンドが送信されること。
   - 同じウィンドウ設定が続いた場合にキャッシュが効いてコマンド送信がスキップされること。

5. **ピクセル送信 (`write_pixels`)**
   - `pigpio.spi_write` がデータ分割（チャンキング）を伴って呼ばれること（モック等でチャンクサイズを制御して確認）。

6. **全画面描画 (`display`)**
   - 画像がリサイズされ、RGB565変換され、`set_window` 呼び出し後に `write_pixels` されること。

7. **部分描画 (`display_region`)**
   - 指定領域でクリッピングされ、変換後に部分更新が行われること。
   - 無効な領域（サイズ0など）では何も行わないこと。

8. **電源・終了処理**
   - `sleep`, `wake`, `dispoff`: 対応するコマンドとバックライト制御が行われること。
   - `close`: SPI クローズとバックライト消灯が行われること。

## 実装ステップ

1. `tests/test_03_st7789v.py` を作成し、必要な import と定数定義を行う。
2. ヘルパー関数 `create_st7789v_instance` を作成する。
3. 各テストケースを実装する。

## 検証計画

- `mise run test` を実行し、新規作成したテストを含む全テストがパスすることを確認します。
