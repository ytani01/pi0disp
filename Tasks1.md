# `tests/test_01_disp_base.py` 再改善タスク

`Plan.md` に基づき、以下のタスクを順番に実行する。

## 1. ヘルパーメソッドの追加

- [x] `_setup_pi_mock` ヘルパーメソッドを `TestDispBase` クラスに追加する。

## 2. テストメソッドのリファクタリング

- [x] `test_init_success` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_init_pigpio_connection_error` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_init_display` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_set_rotation_to_90` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_set_rotation_to_0` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_display_resizes_image` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_display_with_correct_size_image` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_close_calls_pi_stop_when_connected` をリファクタリングし、`_setup_pi_mock` を使用する。
- [x] `test_close_does_not_call_pi_stop_when_not_connected` をリファクタリングし、`_setup_pi_mock` を使用する。

## 3. 最終確認

- [x] `uv run pytest tests/test_01_disp_base.py` を実行し、すべてのテストがパスすることを確認する。
- [x] `mise run lint` を実行し、リンターエラーが出ないことを確認する。
