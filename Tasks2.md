# `tests/test_01_disp_base.py` 最終改善タスク

`Plan2.md` に基づき、以下のタスクを順番に実行する。

## 1. `setUp` メソッドの修正

- [x] `setUp` メソッドを修正し、`self._setup_pi_mock()` を呼び出して `self.mock_pi_instance` を設定する。

## 2. テストメソッドの簡素化

- [x] `test_init_success` から `_setup_pi_mock` の呼び出しを削除する。
- [x] `test_init_display` から `_setup_pi_mock` の呼び出しを削除する。
- [x] `test_set_rotation_to_90` から `_setup_pi_mock` の呼び出しを削除する。
- [x] `test_set_rotation_to_0` から `_setup_pi_mock` の呼び出しを削除する。
- [x] `test_display_resizes_image` から `_setup_pi_mock` の呼び出しを削除する。
- [x] `test_display_with_correct_size_image` から `_setup_pi_mock` の呼び出しを削除する。
- [x] `test_close_calls_pi_stop_when_connected` から `_setup_pi_mock` の呼び出しを削除し、`self.mock_pi_instance` を使用するように修正する。
- [x] `test_close_does_not_call_pi_stop_when_not_connected` から `_setup_pi_mock` の呼び出しを削除し、`self.mock_pi_instance` を使用するように修正する。

## 3. 最終確認

- [x] `uv run pytest tests/test_01_disp_base.py` を実行し、すべてのテストがパスすることを確認する。
- [x] `mise run test` を実行し、リンターエラーが出ないことを確認する。