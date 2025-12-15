# `src/pi0disp/disp/disp_spi.py` のテストタスク

`Plan5.md` に基づき、`tests/test_02_disp_spi.py` を作成するための以下のタスクを順番に実行する。

## 1. テストファイルの基本構造の作成

- [ ] `tests/test_02_disp_spi.py` ファイルを作成する。
- [ ] 必要なモジュールをインポートする (`unittest`, `unittest.mock`, `time`, `pigpio`, `DispSpi`, `DispBase`)。
- [ ] `TestDispSpi` クラスを `unittest.TestCase` から継承して作成する。
- [ ] `if __name__ == '__main__':` ブロックを追加し、`unittest.main()` を呼び出す。

## 2. `setUp` およびモック設定の準備

- [ ] `TestDispSpi.setUp` メソッドを実装する。
    - [ ] `super().setUp()` を呼び出す。
    - [ ] `time.sleep` をモック化するための `patcher_sleep` を追加し、`self.addCleanup` で停止するように設定する。
    - [ ] `DispSpi` 固有のデフォルト値（`default_channel`, `default_speed_hz`, `default_pin`）を定義する。

## 3. ヘルパーメソッドの導入

- [ ] `_create_disp_spi_instance` ヘルパーメソッドを `TestDispSpi` クラスに追加する。
    - [ ] `size`, `rotation`, `bl_at_close`, `channel`, `pin`, `speed_hz`, `debug` の引数を定義する。
    - [ ] `pigpio_connected=True`, `spi_open_handle=0` の引数を定義する。
    - [ ] `DispSpi` インスタンスを生成して返す。

## 4. `__init__` メソッドのテスト

- [ ] **`test_init_success`** のテストメソッドを実装する。
    - [ ] `_create_disp_spi_instance` を使用して `DispSpi` インスタンスを生成する。
    - [ ] `self.mock_pigpio.pi.assert_called_once()` をアサートする。
    - [ ] `self.mock_pi_instance.set_mode` が各ピンに対して `pigpio.OUTPUT` で呼び出されたことをアサートする。
    - [ ] `self.mock_pi_instance.spi_open` が正しい引数で呼び出されたことをアサートする。
    - [ ] インスタンス変数 (`bl_at_close`, `pin`, `spi_handle`) が正しく設定されていることをアサートする。
- [ ] **`test_init_spi_open_error`** のテストメソッドを実装する。
    - [ ] `_create_disp_spi_instance` を `spi_open_handle=-1` で呼び出す。
    - [ ] `RuntimeError` が発生することを確認する。

## 5. その他のメソッドのテスト

- [ ] **`test_enter_exit_context_manager`** のテストメソッドを実装する。
    - [ ] `with _create_disp_spi_instance(...) as disp:` 構文を使用し、`__exit__` が `self.close()` を呼び出すことを確認する。
- [ ] **`test_write_command`** のテストメソッドを実装する。
    - [ ] `_write_command` を呼び出し、`self.mock_pi_instance.write(dc_pin, 0)` と `self.mock_pi_instance.spi_write` が呼び出されたことをアサートする。
- [ ] **`test_write_data_int`** のテストメソッドを実装する。
    - [ ] `_write_data` を `int` で呼び出し、`self.mock_pi_instance.write(dc_pin, 1)` と `self.mock_pi_instance.spi_write` が呼び出されたことをアサートする。
- [ ] **`test_write_data_bytes_list`** のテストメソッドを実装する。
    - [ ] `_write_data` を `bytes` または `list` で呼び出し、`self.mock_pi_instance.write(dc_pin, 1)` と `self.mock_pi_instance.spi_write` が呼び出されたことをアサートする。
- [ ] **`test_init_display`** のテストメソッドを実装する。
    - [ ] `init_display` を呼び出し、`super().init_display()` が呼び出されたことを確認する。
    - [ ] `self.mock_pi_instance.write` が `rst` および `bl` ピンに対して正しいシーケンスで呼び出されたことをアサートする。
    - [ ] `self.mock_sleep.sleep` が正しい引数で呼び出されたことをアサートする。
- [ ] **`test_close`** のテストメソッドを実装する。
    - [ ] `close()` を呼び出し、`self.mock_pi_instance.spi_close()` が呼び出されたことをアサートする。
    - [ ] `super().close()` が呼び出されたことをアサートする。
    - [ ] `bl` 引数と `bl_at_close` の組み合わせによるバックライト制御の挙動をテストする。

## 6. 最終確認

- [ ] `uv run pytest tests/test_02_disp_spi.py` を実行し、すべてのテストがパスすることを確認する。
- [ ] `mise run test` を実行し、リンターエラーが出ないことを確認する。
