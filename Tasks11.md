# Tasks 11: Fixture Consolidation and Cleanup

- [x] 共通フィクスチャを `tests/conftest.py` に移動する <!-- id: 0 -->
  - [x] `mock_pi_constructor` (from `test_01_disp_base.py`)
  - [x] `mock_logger` (from `test_01_disp_base.py`)
  - [x] `mock_pi_instance` (from `test_01_disp_base.py`)
- [x] テストファイルを修正してローカルフィクスチャを削除する <!-- id: 1 -->
  - [x] `tests/test_01_disp_base.py`
  - [x] `tests/test_02_disp_spi.py`
- [x] 未使用ファイルを削除する <!-- id: 2 -->
  - [x] `tests/_pigpio_mock.py`
- [x] 変更を検証する <!-- id: 3 -->
  - [x] `mise run test` を実行する
