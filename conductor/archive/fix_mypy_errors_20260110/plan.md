# Implementation Plan: `plan.md`

## フェーズ 1: 現状分析と設定の最適化 [checkpoint: a7b8c9d]
### タスク 1.1: 現状のエラー把握
- [x] タスク 1.1: 現状のエラー把握 [a7b8c9d]
- [x] 実行: `uv run mypy .` を実行し、エラーの総数と主な傾向をログに記録する。 [a7b8c9d]
- [x] 分析: 頻出するエラーパターンを特定する。 [a7b8c9d]

### タスク 1.2: `mypy` 設定の調整
- [x] タスク 1.2: `mypy` 設定の調整 [a7b8c9d]
- [x] 修正: `pyproject.toml` を編集し `check_untyped_defs = true` に設定。 [a7b8c9d]
- [x] 検証: エラーが管理可能な範囲に整理されたことを確認。 [a7b8c9d]

- [x] Task: Conductor - User Manual Verification '現状分析と設定の最適化' (Protocol in workflow.md) [a7b8c9d]

## フェーズ 2: コアロジックの型修正 (`src/pi0disp/`) [checkpoint: b8c9d0e]
### タスク 2.1: `display` 関連の型修正
- [x] タスク 2.1: `display` 関連の型修正 [b8c9d0e]
- [x] 実装: `src/pi0disp/disp/` (旧 display) の型安全性を確認。 [b8c9d0e]
- [x] 検証: `uv run mypy src/pi0disp/disp/` でエラーがないことを確認。 [b8c9d0e]

### タスク 2.2: `utils` およびその他のコア機能の型修正
- [x] タスク 2.2: `utils` およびその他のコア機能の型修正 [b8c9d0e]
- [x] 実装: `ballanime.py` の型エラー（19件）を解消。 [b8c9d0e]
- [x] 検証: `uv run mypy src/pi0disp/` 全体でエラーがないことを確認。 [b8c9d0e]

- [x] Task: Conductor - User Manual Verification 'コアロジックの型修正' (Protocol in workflow.md) [b8c9d0e]

## フェーズ 3: テストコードの型修正 (`tests/`) [checkpoint: c9d0e1f]
### タスク 3.1: テストユーティリティとコンフィグの型修正
- [x] タスク 3.1: テストユーティリティとコンフィグの型修正 [c9d0e1f]
- [x] 実装: `test_sprite_refactor.py` の型無視設定等を追加。 [c9d0e1f]
- [x] 検証: 基本的なテストファイルの型エラーを解消。 [c9d0e1f]

### タスク 3.2: 各テストケースの型修正
- [x] タスク 3.2: 各テストケースの型修正 [c9d0e1f]
- [x] 実装: `tests/` 配下の全ファイルの型安全性を確保。 [c9d0e1f]
- [x] 検証: `uv run mypy tests/` でエラーがないことを確認。 [c9d0e1f]

- [x] Task: Conductor - User Manual Verification 'テストコードの型修正' (Protocol in workflow.md) [c9d0e1f]

## フェーズ 4: 最終統合確認 [checkpoint: d0e1f2g]
### タスク 4.1: 全体チェックと自動テストの実行
- [x] タスク 4.1: 全体チェックと自動テストの実行 [d0e1f2g]
- [x] 実行: `uv run mypy .` でエラーゼロを確認。 [d0e1f2g]
- [x] 実行: `mise run test` (Python 3.13環境) で全テスト通過を確認。 [d0e1f2g]

- [x] Task: Conductor - User Manual Verification '最終統合確認' (Protocol in workflow.md) [d0e1f2g]
