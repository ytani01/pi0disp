# Implementation Plan: Complete Lint Pass for `samples` and Integration

`samples` ディレクトリのエラーを解消し、プロジェクト全体で `mise run lint` が完全にパスする状態を確立する。

## Phase 1: Samples Directory Cleanup [checkpoint: 1bd630d]
`samples` 配下の残存する型エラーの解消。

- [x] Task: `samples/lcd_check.py` の修正 (2300a1b)
    - [x] 根本原因調査：`rotation` が `None` になり得る取得元の特定
    - [x] 修正：適切な型キャストまたはガード節の追加
- [x] Task: `samples` ディレクトリ全体の再スキャンと微調整 (2300a1b)
    - [x] `uv run basedpyright samples` を実行し、0 errors を確認
    - [x] `uv run mypy samples` を実行し、整合性を確認
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Project-wide Integration and Final Pass
全ディレクトリ（src, samples）を統合した最終検証。

- [ ] Task: `mise run lint` の完遂
    - [ ] 依存タスク `upgradeproject` を含む全工程の実行
    - [ ] `ruff`, `basedpyright`, `mypy` の全パスを確認
- [ ] Task: 既存機能のデグレード確認
    - [ ] `uv run pytest tests` を実行し、全テストのパスを確認（ハードウェア依存分を除く）
- [ ] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)
