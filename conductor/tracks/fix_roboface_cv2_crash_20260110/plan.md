# Plan: `plan.md`

## 開発原則: 憶測厳禁
1. 推測厳禁。事実に基づき根本原因を突き止める。
2. デバッグログや print を活用し、効率的に原因を特定する。
3. 可能な限り自動テストを実施する。

## Phase 1: Analysis and Reproduction (Red Phase) [checkpoint: fe6caca]
- [x] Task: `samples/roboface.py` の `DisplayBase` および `CV2Disp` の現在の実装を確認する
- [x] Task: `TypeError` を再現するユニットテスト（モックを使用）を `tests/test_roboface_disp.py` として作成し、失敗（Red）を確認する
- [x] Task: Conductor - User Manual Verification 'Phase 1: Analysis and Reproduction' (Protocol in workflow.md)

## Phase 2: Implementation (Green Phase) [checkpoint: 55a8e22]
- [x] Task: `samples/roboface.py` の `DisplayBase.display` および `CV2Disp.display` のシグネチャを修正し、`full` 引数を受け取れるようにする
- [x] Task: 作成したテストを実行し、パスすることを確認する
- [x] Task: `Lcd.display` の実装も確認し、一貫性が保たれているかチェックする（必要に応じて修正）
- [x] Task: Conductor - User Manual Verification 'Phase 2: Implementation' (Protocol in workflow.md)

## Phase 3: Quality Gate and Cleanup
- [ ] Task: `ruff` および `mypy` を実行し、静的解析エラーがないことを確認する
- [ ] Task: プロジェクト全体のテストを実行し、デグレがないことを確認する
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Quality Gate and Cleanup' (Protocol in workflow.md)
