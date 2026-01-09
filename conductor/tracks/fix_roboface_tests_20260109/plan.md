# Implementation Plan: roboface テストの整理

## フェーズ 1: テストファイルの整理と修正
- [~] **タスク 1.1:** `roboface1.py` と `roboface2.py` に関連するテストファイルを特定し、削除する。
- [ ] **タスク 1.2:** `test_23_roboface2.py` を `test_roboface.py` にリネームする。
- [ ] **タスク 1.3:** `test_roboface.py` の内容を修正し、テスト対象を `samples/roboface.py` に変更する。
- [ ] **タスク 1.4:** `test_24_roboface2_thread.py` と `test_25_roboface2_queue.py` の内容を確認し、`roboface.py` に合わせて修正、または不要であれば削除する。
- [ ] **タスク 1.5:** `test_debug_roboface.py` の内容を確認し、`roboface.py` に合わせて修正、または不要であれば削除する。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 1' (Protocol in workflow.md)**

## フェーズ 2: 最終確認
- [ ] **タスク 2.1:** `uv run test` を実行し、すべてのテストがパスすることを確認する。
- [ ] **タスク 2.2:** コードレビューを行い、古いファイルへの参照が残っていないことを確認する。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 2' (Protocol in workflow.md)**
