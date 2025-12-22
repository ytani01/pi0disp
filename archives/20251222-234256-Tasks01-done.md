# 実行タスクリスト

- [x] `tests/test_13_cmd_bl.py` を読み込む。
- [x] `tests/test_13_cmd_bl.py` の `test_config_nonzero` 関数のインデントエラーを修正する。
- [x] `tests/test_13_cmd_bl.py` に `test_config_zero_from_conf` および `test_pigpio_connection_failure` 関数を追加する。
    - [x] `test_clamp_with_config` の後に `test_config_zero_from_conf` 関数を追記する。
    - [x] `test_config_zero_from_conf` の後に `test_pigpio_connection_failure` 関数を追記する。
- [x] `tests/test_13_cmd_bl.py` 内の `test_pigpio_connection_failure` 関数のテスト修正タスク:
    - [x] `test_pigpio_connection_failure` 関数から `with pytest.raises(RuntimeError):` ブロックを削除する。
    - [x] `result.exception` が `RuntimeError` のインスタンスであることをアサートする。
    - [x] `result.exit_code` が `0` であることをアサートする。
    - [x] エラーメッセージ "Could not connect to pigpio daemon. Is it running?" が `result.output` に含まれていることをアサートする。
- [x] 修正した `tests/test_13_cmd_bl.py` を保存する。
- [x] `uv run pytest tests/test_13_cmd_bl.py` を実行して、テストがパスし、カバレッジが100%になることを確認する。