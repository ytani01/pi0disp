# Plan01.md

## `test_pigpio_connection_failure` の修正

### 問題点
`test_pigpio_connection_failure` テストが失敗する。`bl_cmd` 内で `RuntimeError` が発生しているにも関わらず、`click.testing.CliRunner` の `invoke` メソッドが `exit_code=0` を返しているため。これは `bl_cmd` が例外を捕捉し、システム終了コードに変換していないため。

### 修正計画
1.  `tests/test_13_cmd_bl.py` ファイルを開く。
2.  `test_pigpio_connection_failure` 関数を修正する。
3.  `runner.invoke(bl_cmd, [str(brightness)])` の呼び出しを `runner.invoke(bl_cmd, [str(brightness)], catch_exceptions=False)` に変更する。
4.  `assert result.exit_code == 1` の行を削除し、`with pytest.raises(RuntimeError):` を使用して、`bl_cmd` が `RuntimeError` を発生させることを検証する。

