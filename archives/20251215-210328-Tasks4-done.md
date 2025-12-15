# `tests/test_01_disp_base.py` テストコード改善タスク

`Plan4.md` に基づき、以下のタスクを順番に実行する。

## 1. `_create_disp_base_instance` ヘルパーメソッドの追加

- [x] `_create_disp_base_instance` ヘルパーメソッドを `TestDispBase` クラスに追加する。

## 2. テストメソッドの修正

- [x] `test_init_success` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_init_pigpio_connection_error` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_init_display` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_set_rotation_to_90` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_set_rotation_to_0` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_display_resizes_image` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_display_with_correct_size_image` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_close_calls_pi_stop_when_connected` を `_create_disp_base_instance` を使用するように修正する。
- [x] `test_close_does_not_call_pi_stop_when_not_connected` を `_create_disp_base_instance` を使用するように修正する。

## 3. 最終確認

- [x] `uv run pytest tests/test_01_disp_base.py` を実行し、すべてのテストがパスすることを確認する。
- [x] `mise run test` を実行し、リンターエラーが出ないことを確認する。