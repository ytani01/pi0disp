# Plan 12: Final Cleanup

`tests/` 以下の最終確認を行った結果、`tests/test_02_disp_spi.py` に以前のリファクタリング時の古いコメント（`self.mock_pi_instance...` など）が残っていることがわかりました。
これらは現在のコードと整合していないため削除します。

## 改善案

### 1. `tests/test_02_disp_spi.py` のクリーンアップ

- `test_close_with_bl_on` メソッド内の古いコメント行を削除します。

## 検証計画

- `mise run test` を実行し、変更が機能に影響を与えないことを確認します。
