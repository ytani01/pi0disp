# Implementation Plan - `samples/roboface2.py` のCPU負荷削減

## Phase 1: 現状分析と計測基盤の整備
- [x] 現状のCPU使用率の計測と記録 (`top`/`htop` によるベースラインの確定)
- [x] `RobotFace` クラスへのFPS制御用パラメータの追加 (`RfConfig` への統合)
- [x] 描画のスキップが必要かどうかを判定するための「状態変化検知」ロジックの設計
- [x] Task: Conductor - User Manual Verification 'Phase 1: 現状分析と計測基盤の整備' (Protocol in workflow.md)

## Phase 2: 最適化ロジックの実装
- [x] `RobotFace.update()` またはメインループへの適切な `time.sleep` の導入
- [x] `RfRenderer` または `RobotFace` における「Dirtyフラグ」の実装
    - 状態（目、眉、視線など）に変更がない場合は描画処理をスキップする
- [x] ディスプレイ送信（SPI）処理の条件付き実行の実装
- [x] Task: Conductor - User Manual Verification 'Phase 2: 最適化ロジックの実装' (Protocol in workflow.md)

## Phase 3: 検証と最終調整
- [x] 最適化適用後のCPU使用率の計測とベースラインとの比較
- [x] アニメーションの滑らかさと応答性の視覚的確認
- [x] `InteractiveMode` での入力に対する反応速度の確認
- [x] リンティングと既存テストの実行
- [x] Task: Conductor - User Manual Verification 'Phase 3: 検証と最終調整' (Protocol in workflow.md)
