## Tasks01.md: `src/pi0disp/disp/disp_base.py` テストカバレッジ100%達成タスクリスト

### 1. 準備
- [x] git branch `feature/Tasks01` を作成する。

### 2. `DispBase.__init__` の `debug` 引数に関するテスト追加
- [x] `tests/test_01_disp_base.py` に、`debug=True` で `DispBase` をインスタンス化する新しいテスト関数 `test_init_with_debug_true` を追加する。
- [x] `test_init_with_debug_true` 内で、`mock_logger` がデバッグレベルのログメッセージ（例: `"size=%s,rotation=%s", size, rotation`）を適切に記録したことをアサートする。

### 3. `rotation` プロパティのsetterの網羅的テスト
- [x] `tests/test_01_disp_base.py` に、`rotation = 180` に設定した場合に `disp_base.size` が `disp_base.native_size` と同じ値になることを確認する新しいテスト関数 `test_set_rotation_to_180` を追加する。
- [x] `tests/test_01_disp_base.py` に、初期回転を `270` に設定し、その後 `rotation = 0` に変更した場合に `disp_base.size` が `disp_base.native_size` と同じ値になることを確認する新しいテスト関数 `test_set_rotation_from_270_to_0` を追加する。

### 4. `display` メソッドのロギングテスト追加
- [x] `tests/test_01_disp_base.py` に、`image.size` が `disp_base.size` と異なる場合に `disp_base.display()` がデバッグログ（例: `"adjust image size"`）を出力することを確認する新しいテスト関数 `test_display_logs_on_resize` を追加する。
- [x] `tests/test_01_disp_base.py` に、`image.size` が `disp_base.size` と同じ場合に `disp_base.display()` がデバッグログ（例: `"adjust image size"`）を出力しないことを確認する新しいテスト関数 `test_display_no_logs_on_no_resize` を追加する。

### 5. `__exit__` メソッドの例外発生時テスト追加
- [x] `tests/test_01_disp_base.py` に、`with` ブロック内で例外（例: `ValueError`）が発生した場合でも `disp_base.close()` が呼ばれ、`pi.stop()` が実行されることを確認する新しいテスト関数 `test_context_manager_with_exception` を追加する。

### 6. `get_display_info` 関数のテスト追加
- [x] `tests/test_01_disp_base.py` に、`get_display_info()` が `MyConf` から `width`, `height`, `rotation` を正しく読み込み、対応する辞書を返すことを確認する新しいテスト関数 `test_get_display_info_with_conf_values` を追加する。
- [x] `tests/test_01_disp_base.py` に、`get_display_info()` が `MyConf` に `width`, `height`, `rotation` が存在しない場合に、辞書の値が `None` になることを確認する新しいテスト関数 `test_get_display_info_with_missing_conf_values` を追加する。
- [x] `tests/test_01_disp_base.py` に、`get_display_info(debug=True)` がデバッグログ（例: `"read config file"` など）を適切に記録することを確認する新しいテスト関数 `test_get_display_info_with_debug_true` を追加する。

### 7. テストとレビュー
- [x] `mise run test` を実行し、追加・修正したテストがすべてパスすることを確認する。
- [x] テストカバレッジレポートを生成し、`src/pi0disp/disp/disp_base.py` のカバレッジが100%になっていることを確認する。
- [x] 必要に応じて、テストコードと対象コードを修正し、`mise run test` がエラーなく終了することを確認する。
