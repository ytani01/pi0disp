# Plan 11: Consolidate Fixtures and Cleanup

`tests/` 以下の最終レビューの結果、以下の改善点が見つかりました。

1. **共通フィクスチャの重複**: `test_01_disp_base.py` と `test_02_disp_spi.py` で、`pigpio` や `logger` のモック作成ロジック（フィクスチャ）が重複しています。
2. **未使用ファイルの存在**: `tests/_pigpio_mock.py` は現在どこからも使用されていません。

これらを整理し、保守性を向上させます。

## 改善案

### 1. 共通フィクスチャの `conftest.py` への移動

以下のフィクスチャを `tests/conftest.py` に移動し、各テストファイルから削除します。

- `mock_pi_constructor`: `pigpio.pi` コンストラクタのモック
- `mock_pi_instance`: `pigpio.pi()` が返すインスタンスのモック
- `mock_logger`: `get_logger` のモック

### 2. テストコードの修正

`tests/test_01_disp_base.py` と `tests/test_02_disp_spi.py` を修正し、`conftest.py` に移動したフィクスチャを自動的に利用するようにします（引数として受け取るだけで機能します）。

### 3. 未使用ファイルの削除

- `tests/_pigpio_mock.py` を削除します。

## 検証計画

- `mise run test` を実行し、すべてのテスト（計33件程度）がパスすることを確認します。
