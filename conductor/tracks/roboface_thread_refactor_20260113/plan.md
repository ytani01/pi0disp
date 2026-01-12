# Implementation Plan: roboface_thread_refactor

## Phase 1: Base Infrastructure & Diagnostic Logging [checkpoint: d911270]
`RfGazeManager` を `RfAnimationEngine` にリネーム・拡張し、憶測を排除するための詳細なログ出力とステータス監視を実装する。

- [x] Task 1: Create Test Suite for Sub-thread Mechanism d911270
- [x] Task 2: Implement Diagnostic Logging & Renaming d911270
- [x] Task 3: Implement Status Monitoring API d911270
- [x] Task 4: Implement Resilient Error Handling d911270
- [x] Task: Conductor - User Manual Verification 'Phase 1: Base Infrastructure & Diagnostic Logging' (Protocol in workflow.md) d911270

## Phase 2: Mode Integration & Concurrency Verification [checkpoint: 941c453]
`AppMode` 派生クラスを新エンジンに対応させ、スレッド間の競合がないことをログと実測値で確認する。

- [x] Task 1: Update `AppMode` to host `RfAnimationEngine` 6d8eba6
- [x] Task 2: Update `RandomMode` & `InteractiveMode` 6d8eba6
- [x] Task 3: Ensure Clean Shutdown 6d8eba6
- [x] Task: Conductor - User Manual Verification 'Phase 2: Mode Integration & Concurrency Verification' (Protocol in workflow.md) 941c453

## Phase 3: Visual Validation & Performance Fact-finding
実機（またはOpenCV）での動作確認に加え、フレームキャプチャを用いて描画の正確性を「証拠」に基づいて検証する。

- [x] Task 1: Integration Testing with Error Injection 941c453
- [x] Task 2: Visual Evidence Verification 941c453
- [x] Task 3: Performance Fact-finding 941c453
- [x] Task: Conductor - User Manual Verification 'Phase 3: Visual Validation & Performance Fact-finding' (Protocol in workflow.md) 941c453
