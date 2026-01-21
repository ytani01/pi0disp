# Implementation Plan - 統合型インタラクティブ LCD 設定ウィザード

このプランは、向き・反転・BGRをすべてリアルタイムに調整可能な統合ウィザードを実装するものです。

## Phase 1: 統合ウィザードロジックの実装
- [x] Task: 統合調整ループの実装 (src/pi0disp/commands/lcd_check.py) [1669c86]
    - [x] `run_unified_wizard(disp, conf)` を作成し、`a-d, i, g, ENTER` の入力を処理する。
    - [x] 設定変更時に `disp._last_img = None` を設定して残像を防止する。
- [x] Task: 設定の一括保存処理の実装 [1669c86]
    - [x] `ENTER` 決定時に `rotation`, `invert`, `bgr` を `update_toml_settings` で一括更新する。
- [x] Task: 動作確認テスト (TDD) [1669c86]
    - [x] `tests/test_28_unified_wizard.py` を作成し、トグル操作と一括保存を検証する。
- [ ] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: 最終統合とクリーンアップ
- [ ] Task: `lcd-check` コマンドの簡略化
    - [ ] 既存の `run_wizard` (Q&A形式) を `run_unified_wizard` に置き換える。
- [ ] Task: ドキュメント更新
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)
