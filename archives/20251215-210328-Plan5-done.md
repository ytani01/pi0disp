# `src/pi0disp/disp/disp_spi.py` のテスト計画 (`Plan5.md`)

`DispSpi` クラス (`src/pi0disp/disp/disp_spi.py`) のユニットテストを作成するための計画を以下に示します。このテストは `tests/test_02_disp_spi.py` として実装します。

`DispSpi` は `DispBase` を継承しているため、`tests/test_01_disp_base.py` で確立されたモックのパターンとヘルパーメソッド（特に `_setup_pi_mock`）を最大限に活用します。

## 1. テストファイルの基本構造の作成

-   `tests/test_02_disp_spi.py` ファイルを作成する。
-   必要なモジュールをインポートする (`unittest`, `unittest.mock`, `time`, `pigpio`, `DispSpi`, `DispBase`)。
-   `TestDispSpi` クラスを `unittest.TestCase` から継承して作成する。
-   `if __name__ == '__main__':` ブロックを追加し、`unittest.main()` を呼び出す。

## 2. `setUp` およびモック設定の準備

-   `TestDispSpi.setUp` メソッドを実装する。
    -   `super().setUp()` を呼び出し、`DispBase` テストで確立された `pigpio` と `mylogger` のモック設定を継承する。これにより、`self.mock_pigpio`, `self.mock_logger_getter`, `self.mock_pi_instance`（デフォルトで接続成功状態）が利用可能になる。
    -   `time.sleep` をモック化するための `patcher_sleep` を追加し、`self.addCleanup` で停止するように設定する。
    -   `DispSpi` 固有のデフォルト値（`default_channel`, `default_speed_hz`, `default_pin`）を定義する。

-   **`_setup_pi_mock` ヘルパーメソッドの継承と調整:**
    -   `TestDispBase` で定義された `_setup_pi_mock` が `pigpio` モックのセットアップを処理するため、`TestDispSpi` ではこれを使用する。

## 3. ヘルパーメソッドの導入

-   `_create_disp_spi_instance` ヘルパーメソッドを `TestDispSpi` クラスに追加する。
    -   このヘルパーは `DispSpi` インスタンスを生成する責任を持つ。
    -   `pigpio.pi().spi_open()` の戻り値 (`spi_handle`) を設定できるようにする引数 `spi_open_handle` を持つ。
    -   `DispSpi` の `__init__` が `super().__init__(size, rotation, debug=debug)` を呼び出すため、`DispBase` のテストと同様に `DispBase` のコンストラクタ引数（`size`, `rotation`, `debug`）を適切に渡せるようにする。
    -   `bl_at_close`, `channel`, `pin`, `speed_hz` などの `DispSpi` 固有の引数も受け取るようにする。

## 4. `__init__` メソッドのテスト

-   **`test_init_success`**:
    *   `_create_disp_spi_instance` を使用して `DispSpi` インスタンスを生成する。
    *   `super().__init__` が正しく呼び出されたことを確認する。（`self.mock_pigpio.pi.assert_called_once()` は `DispBase` のコンストラクタが `pigpio.pi()` を呼ぶことをチェックする）
    *   `self.mock_pi_instance.set_mode` が `pin` ディクショナリ内の各ピンに対して `pigpio.OUTPUT` で呼び出されたことを確認する。
    *   `self.mock_pi_instance.spi_open` が正しい引数（`channel`, `speed_hz`, `0`）で呼び出されたことを確認する。
    *   `self.bl_at_close`, `self.pin`, `self.spi_handle` などのインスタンス変数が正しく設定されていることを確認する。
-   **`test_init_spi_open_error`**:
    *   `_create_disp_spi_instance` を `spi_open_handle=-1` などのエラー値で呼び出す。
    *   `DispSpi` のインスタンス化が `RuntimeError` を発生させることを `with self.assertRaises(RuntimeError):` で確認する。

## 5. その他のメソッドのテスト

-   **`test_enter_exit_context_manager`**:
    *   `with _create_disp_spi_instance(...) as disp:` 構文を使用して、`__enter__` が `self` を返し、`__exit__` が `self.close()` を呼び出すことを確認する。
-   **`test_write_command`**:
    *   `_write_command` を呼び出し、`self.mock_pi_instance.write(dc_pin, 0)` と `self.mock_pi_instance.spi_write` が正しい引数で呼び出されたことを確認する。
-   **`test_write_data_int`**:
    *   `_write_data` を `int` で呼び出し、`self.mock_pi_instance.write(dc_pin, 1)` と `self.mock_pi_instance.spi_write` が正しい引数で呼び出されたことを確認する。
-   **`test_write_data_bytes_list`**:
    *   `_write_data` を `bytes` または `list` で呼び出し、`self.mock_pi_instance.write(dc_pin, 1)` と `self.mock_pi_instance.spi_write` が正しい引数で呼び出されたことを確認する。
-   **`test_init_display`**:
    *   `init_display` を呼び出し、`super().init_display()` が呼び出されたことを確認する。
    *   `self.mock_pi_instance.write` が `rst` ピンおよび `bl` ピンに対して正しいシーケンスで呼び出されたことを確認する。
    *   `self.mock_sleep.sleep` が正しい引数で呼び出されたことを確認する。（`self.mock_sleep` は `time.sleep` のモック）
-   **`test_close`**:
    *   `close()` を呼び出し、`self.mock_pi_instance.spi_close()` が `spi_handle` で呼び出されたことを確認する。
    *   `super().close()` が呼び出されたことを確認する。
    *   `bl` 引数と `bl_at_close` の組み合わせによるバックライト制御の挙動をテストする。
    *   `spi_handle` が無効な場合（例: `spi_open_handle=-1`）に `spi_close` が呼び出されないことをテストする。

## 6. 最終確認

-   `uv run pytest tests/test_02_disp_spi.py` を実行し、すべてのテストがパスすることを確認する。
-   `mise run test` を実行し、リンターエラーが出ないことを確認する。

この計画により、`DispSpi` クラスの主要な機能が、確立されたベストプラクティスと一貫性のある方法で網羅的にテストされます。
