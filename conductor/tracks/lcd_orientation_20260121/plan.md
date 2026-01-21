# Implementation Plan - 統合型インタラクティブ LCD 設定ウィザード

このプランは、向き・反転・BGRをすべてリアルタイムに調整可能な統合ウィザードを実装するものです。

## Phase 1: 統合ウィザードロジックの実装 [checkpoint: 1c91515]
- [x] Task: 統合調整ループの実装 (src/pi0disp/commands/lcd_check.py) (1c91515)
    - [x] `run_unified_wizard(disp, conf)` を作成し、`a-d, i, g, ENTER` および `h, j, k, l` (オフセット) の入力を処理する。
    - [x] 設定変更時に `disp._last_image = None` を設定して残像を防止する。
- [x] Task: 設定の一括保存処理の実装 (1c91515)
    - [x] `ENTER` 決定時に `rotation`, `invert`, `bgr`, `x_offset`, `y_offset` を `update_toml_settings` で一括更新する。
- [x] Task: 動作確認テスト (TDD) (1c91515)
    - [x] `tests/test_28_unified_wizard.py` および `tests/test_31_display_logic_verify.py` でロジックを検証。
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md) (1c91515)

## Phase 2: 最終統合とクリーンアップ [checkpoint: b015580]
- [x] Task: `lcd-check` コマンドの簡略化 (b015580)
    - [x] 既存の `run_wizard` (Q&A形式) を `run_unified_wizard` に置き換え。
- [x] Task: ドキュメント更新 (b015580)
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md) (b015580)
