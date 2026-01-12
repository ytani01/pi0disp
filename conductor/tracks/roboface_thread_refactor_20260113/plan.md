# Implementation Plan: roboface_thread_refactor

## Phase 1: Base Infrastructure & Diagnostic Logging
`RfGazeManager` を `RfAnimationEngine` にリネーム・拡張し、憶測を排除するための詳細なログ出力とステータス監視を実装する。

- [x] Task 1: Create Test Suite for Sub-thread Mechanism
- [x] Task 2: Implement Diagnostic Logging & Renaming
- [x] Task 3: Implement Status Monitoring API
- [x] Task 4: Implement Resilient Error Handling
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Base Infrastructure & Diagnostic Logging' (Protocol in workflow.md)

## Phase 2: Mode Integration & Concurrency Verification
`AppMode` 派生クラスを新エンジンに対応させ、スレッド間の競合がないことをログと実測値で確認する。

- [ ] Task 1: Update `AppMode` to host `RfAnimationEngine`
- [ ] Task 2: Update `RandomMode` & `InteractiveMode`
- [ ] Task 3: Ensure Clean Shutdown
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Mode Integration & Concurrency Verification' (Protocol in workflow.md)

## Phase 3: Visual Validation & Performance Fact-finding
実機（またはOpenCV）での動作確認に加え、フレームキャプチャを用いて描画の正確性を「証拠」に基づいて検証する。

- [ ] Task 1: Integration Testing with Error Injection
- [ ] Task 2: Visual Evidence Verification
- [ ] Task 3: Performance Fact-finding
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Visual Validation & Performance Fact-finding' (Protocol in workflow.md)
