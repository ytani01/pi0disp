# Implementation Plan - 目の動きをスレッド化

## Phase 1: 基盤整備とスレッドクラスの設計
- [x] `RfConfig` へのスレッドパラメータの追加 [checkpoint: a1b2c3d]
- [x] `RfGazeManager` クラスの新規実装 [checkpoint: a1b2c3d]
- [x] Phase 1 動作確認 (単体テスト) [checkpoint: a1b2c3d]

## Phase 2: RobotFace への統合
- [x] `RobotFace` でのスレッド管理の実装 [checkpoint: b2c3d4e]
    - コンストラクタでの生成。
    - `start()`, `stop()` メソッドの追加。
- [x] `RfUpdater` との責務分担の整理 [checkpoint: b2c3d4e]
    - 視線移動ロジックを `RfGazeManager` に完全移行。
- [x] Phase 2 動作確認 (RobotFaceとの統合) [checkpoint: b2c3d4e]

## Phase 3: アプリケーション層の適合と動作確認
- [x] `InteractiveMode` の修正 [checkpoint: c3d4e5f]
    - `input()` 待ちの間も背景で目が動くことを確認。
- [x] `RandomMode` の修正 [checkpoint: c3d4e5f]
    - 視線管理をスレッドに任せ、メインループを簡素化。
- [x] 結合テストと最終確認 [checkpoint: c3d4e5f]
- [x] Phase 3 最終動作確認 [checkpoint: c3d4e5f]
