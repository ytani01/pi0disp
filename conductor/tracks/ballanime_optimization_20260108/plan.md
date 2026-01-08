# 実装計画 - ballanime_optimization_20260108

## フェーズ 1: 構造のリファクタリングとモード追加
- [x] **タスク 1.1: クリックコマンドへのオプション追加** (6c3f420)
    - `src/pi0disp/commands/ballanime.py` の `ballanime` コマンドに `--mode [simple|fast]` オプションを追加し、デフォルトを `simple` に設定する。
- [x] **タスク 1.2: ループ関数の分離** (2e39287)
    - 現在の `_main_loop_optimized` を参考に、`_loop_simple` と `_loop_fast` の 2 つの関数に分離し、モードに応じて呼び分ける構造にする。
- [x] **Task: Conductor - User Manual Verification 'フェーズ 1' (Protocol in workflow.md)**

## フェーズ 2: Simple モードの実装（簡略化）
- [x] **タスク 2.1: 不要なロジックの削ぎ落とし** (2e39287)
    - `_loop_simple` 内から `dirty_regions` の計算、`RegionOptimizer.merge_regions`、`lcd.display_region` などの手動更新ロジックをすべて削除する。
- [x] **タスク 2.2: 自動差分更新への移行** (2e39287)
    - 描画済みの Image オブジェクトを `lcd.display(image)` に渡すだけのシンプルな実装に変更する。
- [x] **Task: Conductor - User Manual Verification 'フェーズ 2' (Protocol in workflow.md)**

## フェーズ 3: Fast モードの実装（極限最適化）
- [x] **タスク 3.1: 背景キャッシュの導入** (2e39287)
    - `_loop_fast` において、背景の生成・コピーコストを削減するために背景画像をキャッシュし、`copy()` して使い回す方式を徹底する。
- [~] **タスク 3.2: 手動領域計算の洗練**
    - ボールの移動前後の領域を統合し、ドライバの差分検知をバイパスする `display_region` 呼び出しが最適に行われるように調整する。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 3' (Protocol in workflow.md)**

## フェーズ 4: パフォーマンス比較テストの構築
- [ ] **タスク 4.1: 計測用テストスクリプトの作成**
    - `tests/test_performance.py` を拡張（または新規作成）し、両モードを一定時間実行して CPU 負荷と平均 FPS を取得・表示するテストを実装する。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 4' (Protocol in workflow.md)**