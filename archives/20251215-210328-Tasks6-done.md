# `tests/test_02_disp_spi.py` 改善タスク (第2版)

## 1. モック戦略の簡素化と明確化

-   [x] **1.1 `DispBase.close` のパッチ方法の簡素化:**
    -   [x] `setUp` から `self.patcher_disp_base_close` (およびその関連する初期化とクリーンアップ) を削除する。
    -   [x] `test_close` および `test_enter_exit_context_manager` で `DispSpi.close` を `patch.object` し、それが呼び出されたことをアサートする。

## 2. `_create_disp_spi_instance` ヘルパーの最適化

-   [ ] **2.1 デフォルト値の処理の簡素化:**
    -   [x] `_create_disp_spi_instance` ヘルパーから `actual_channel`, `actual_speed_hz`, `actual_pin` の計算ロジックを削除する。

## 3. テストの網羅性と正確性の向上

-   [ ] **3.1 `test_init_success` で `DispBase.__init__` の呼び出しを検証:**
    -   [x] `setUp` で `pi0disp.disp.disp_base.DispBase.__init__` をモックする (`self.patcher_disp_base_init` と `self.mock_disp_base_init` を設定する)。
    -   [x] `_simple_disp_base_init_side_effect` メソッドを再度追加し、`obj_self.pi = self.mock_pi_instance` および `obj_self.__log = self.mock_logger_instance` などを設定するようにする。
    -   [x] `test_init_success` および `test_init_custom_pin` で `self.mock_pigpio_pi_class.assert_called_once()` のアサートを削除し、`self.mock_disp_base_init.assert_called_once_with(...)` で置き換える。
    -   [x] `test_init_spi_open_error` にも `self.mock_disp_base_init.assert_called_once_with(...)` を追加する。

-   [ ] **3.2 冗長なアサートの削除:**
    -   [x] `test_init_success` 内の `self.assertEqual(disp.pin, self.default_pin)` の重複しているアサートを一つ削除する。