# Plan 9: Final Polish and Bug Fix for `tests/test_02_disp_spi.py`

`tests/test_02_disp_spi.py` の最終レビューにて、アサーションに関する問題と不整合が見つかりました。これらを修正し、テストの信頼性を確保します。

## 改善案

### 1. `test_init_spi_open_error` における到達不能コードの修正 [重要]

`pytest.raises` ブロック内で例外が発生する行の後にアサーション記述されているため、そのアサーションが実行されていません。

- **現状**:
  ```python
  with pytest.raises(RuntimeError):
      disp = create_disp_spi_instance(size=size)  # ここで例外発生
      mock_disp_base_init.assert_called_once_with(...)  # <--- 実行されない！
  ```

- **修正案**: アサーションを `with` ブロックの外に出します。

### 2. `test_close_with_bl_on` のアサーション強化

`test_close_with_bl_on` において、`mock_pi_instance.stop.assert_called()` が使用されていますが、フィクスチャによる分離が保証されているため、より厳密な `assert_called_once()` に変更します。他のテストメソッド（`test_close_with_bl_off`）との整合性も取れます。

- **現状**: `self.mock_pi_instance.stop.assert_called()`
- **修正案**: `mock_pi_instance.stop.assert_called_once()`

## 次のステップ

上記の修正を行い、最終確認としてテストを実行します。
