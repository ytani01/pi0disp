# Tasks 13: Implement `tests/test_03_st7789v.py`

- [x] `tests/test_03_st7789v.py` の雛形を作成する <!-- id: 0 -->
  - [x] imports, constants
  - [x] `mock_sleep` fixture
  - [x] `mock_optimizer_pack` fixture (if needed)
  - [x] `create_st7789v_instance` helper
- [ ] テストケースを実装する <!-- id: 1 -->
  - [x] `test_init_success` (初期化)
  - [x] `test_init_display` (ハードウェア初期化シーケンス)
  - [x] `test_set_rotation` (回転設定)
  - [x] `test_set_window` (ウィンドウ設定とキャッシュ)
  - [x] `test_write_pixels` (ピクセル送信とチャンキング)
  - [x] `test_display` (全画面描画)
  - [x] `test_display_region` (部分描画)
  - [x] `test_power_management` (sleep, wake, dispoff)
  - [x] `test_close` (終了処理)
- [x] 変更を検証する <!-- id: 2 -->
  - [x] `mise run test` を実行する
