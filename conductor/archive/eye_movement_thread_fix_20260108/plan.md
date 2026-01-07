# 実装計画 - 目の動きをスレッド化の修正

## フェーズ 1: キュー通信の基盤実装 [checkpoint: 0ac6014]
- [x] `RfGazeManager` に `queue.Queue` による受信メカニズムを追加
- [x] 停止命令 (`"exit"`) による安全なスレッド終了処理の実装
- [x] 表情文字列のパースと状態更新のロジックをスレッドループ内に統合
- [x] Task: ユニットテストによるキュー経由の表情更新の検証
- [x] Task: Conductor - User Manual Verification 'フェーズ 1: キュー通信の基盤実装' (Protocol in workflow.md)

## フェーズ 2: RobotFace との統合とバグ修正 [checkpoint: 9dd159d]
- [x] `RobotFace` クラスの修正: 視線スレッドへの命令送信をキュー経由に変更
- [x] インタラクティブモードでのパーツ非表示バグの調査と修正
    - `RfGazeManager` または `RfUpdater` での描画ループと状態保持の整合性を確認
- [x] `RandomMode` の修正: ランダムな表情変更もキュー経由で行うよう適合
- [x] Task: 結合テスト (`tests/test_24_roboface2_thread.py` 等) による動作確認
- [x] Task: Conductor - User Manual Verification 'フェーズ 2: RobotFace との統合とバグ修正' (Protocol in workflow.md)

## フェーズ 3: 最終確認とクリーンアップ
- [x] 実際のハードウェアまたはモック環境での長時間動作確認
- [x] 未使用になった古い通信用メソッドや変数の削除
- [x] ドキュメント（必要であれば `ST7789V-manual.md` など）の更新確認
- [x] Task: Conductor - User Manual Verification 'フェーズ 3: 最終確認とクリーンアップ' (Protocol in workflow.md)
