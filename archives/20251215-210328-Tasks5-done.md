# `src/pi0disp/disp/disp_spi.py` のテストタスク

`Plan5.md` に基づき、`tests/test_02_disp_spi.py` を作成するための以下のタスクを順番に実行する。

## 1. テストファイルの基本構造の作成

- [x] `tests/test_02_disp_spi.py` ファイルを作成する。
- [x] 必要なモジュールをインポートする (`unittest`, `unittest.mock`, `time`, `pigpio`, `DispSpi`, `DispBase`)。
- [x] `TestDispSpi` クラスを `unittest.TestCase` から継承して作成する。
- [x] `if __name__ == '__main__':` ブロックを追加し、`unittest.main()` を呼び出す。

## 2. `setUp` およびモック設定の準備

- [x] `TestDispSpi.setUp` メソッドを実装する。
    - [x] `super().setUp()` を呼び出す。
    - [x] `time.sleep` をモック化するための `patcher_sleep` を追加し、`self.addCleanup` で停止するように設定する。
    - [x] `DispSpi` 固有のデフォルト値（`default_channel`, `default_speed_hz`, `default_pin`）を定義する。

## 3. ヘルパーメソッドの導入

- [x] `_create_disp_spi_instance` ヘルパーメソッドを `TestDispSpi` クラスに追加する。
    - [x] `size`, `rotation`, `bl_at_close`, `channel`, `pin`, `speed_hz`, `debug` の引数を定義する。
    - [x] `pigpio_connected=True`, `spi_open_handle=0` の引数を定義する。
    - [x] `DispSpi` インスタンスを生成して返す。

## 4. `__init__` メソッドのテスト

- [x] **`test_init_success`** のテストメソッドを実装する。
    - [x] `_create_disp_spi_instance` を使用して `DispSpi` インスタンスを生成する。
    - [x] `self.mock_pigpio.pi.assert_called_once()` をアサートする。
    - [x] `self.mock_pi_instance.set_mode` が各ピンに対して `pigpio.OUTPUT` で呼び出されたことをアサートする。
    - [x] `self.mock_pi_instance.spi_open` が正しい引数で呼び出されたことをアサートする。
    - [x] インスタンス変数 (`bl_at_close`, `pin`, `spi_handle`) が正しく設定されていることをアサートする。
- [x] **`test_init_spi_open_error`** のテストメソッドを実装する。
    - [x] `_create_disp_spi_instance` を `spi_open_handle=-1` で呼び出す。
    - [x] `RuntimeError` が発生することを確認する。

## 5. その他のメソッドのテスト

- [x] **`test_enter_exit_context_manager`** のテストメソッドを実装する。
    - [x] `with _create_disp_spi_instance(...) as disp:` 構文を使用し、`__exit__` が `self.close()` を呼び出すことを確認する。
- [x] **`test_write_command`** のテストメソッドを実装する。
    - [x] `_write_command` を呼び出し、`self.mock_pi_instance.write(dc_pin, 0)` と `self.mock_pi_instance.spi_write` が呼び出されたことをアサートする。
- [x] **`test_write_data_int`** のテストメソッドを実装する。
    - [x] `_write_data` を `int` で呼び出し、`self.mock_pi_instance.write(dc_pin, 1)` と `self.mock_pi_instance.spi_write` が呼び出されたことをアサートする。
- [x] **`test_write_data_bytes_list`** のテストメソッドを実装する。
    - [x] `_write_data` を `bytes` または `list` で呼び出し、`self.mock_pi_instance.write(dc_pin, 1)` と `self.mock_pi_instance.spi_write` が呼び出されたことをアサートする。
- [x] **`test_init_display`** のテストメソッドを実装する。
    - [x] `init_display` を呼び出し、`super().init_display()` が呼び出されたことを確認する。
    - [x] `self.mock_pi_instance.write` が `rst` および `bl` ピンに対して正しいシーケンスで呼び出されたことをアサートする。
    - [x] `self.mock_sleep.sleep` が正しい引数で呼び出されたことをアサートする。
- [x] **`test_close`** のテストメソッドを実装する。
    - [x] `close()` を呼び出し、`self.mock_pi_instance.spi_close()` が呼び出されたことをアサートする。
    - [x] `super().close()` が呼び出されたことをアサートする。
    - [x] `bl` 引数と `bl_at_close` の組み合わせによるバックライト制御の挙動をテストする。

## 6. 最終確認

- [x] `uv run pytest tests/test_02_disp_spi.py` を実行し、すべてのテストがパスすることを確認する。
- [x] `mise run test` を実行し、リンターエラーが出ないことを確認する。
