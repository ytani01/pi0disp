# 実装計画 (`plan.md`) - roboface3_cpu_optimization

## フェーズ 1: 現状の徹底分析と計測環境の整備
- [ ] **タスク 1.1: パフォーマンス計測ベースラインの確立**
    - `tests/test_performance.py` を実行し、`roboface2.py` の詳細なCPU/メモリ使用率の基準値を取得・記録する。
- [ ] **タスク 1.2: コードレベルのプロファイリング実行**
    - `cProfile` または `py-spy` を使用し、`roboface2.py` の実行時における関数ごとの処理時間を計測し、真のボトルネックを特定する。
- [ ] **タスク 1.3: 詳細ログ機能の追加 (検証用)**
    - `roboface2.py` のコピーを作成し、各描画・計算工程（画像生成、差分比較、通信送信）の実行時間をマイクロ秒単位で出力するデバッグコードを挿入し、実機での挙動を確認する。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 1' (Protocol in workflow.md)**

## フェーズ 2: roboface3.py の骨格作成と基本的最適化
- [ ] **タスク 2.1: 新規ファイル `samples/roboface3.py` の作成**
    - `roboface2.py` からコードを移植し、`roboface3.py` として動作することを確認する。
- [ ] **タスク 2.2: 重複計算の排除とキャッシュの導入**
    - フェーズ1で特定された計算負荷の高い箇所（背景描画、静的パーツなど）に、効率的なキャッシュ機構を導入する。
- [ ] **タスク 2.3: 描画・更新頻度の最適化**
    - 無駄な再描画（変化がない場合の `draw()` 呼び出し）を上位レベルで確実に防ぐガードロジックを実装する。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 2' (Protocol in workflow.md)**

## フェーズ 3: 通信と差分更新の高度な最適化
- [ ] **タスク 3.1: 差分検出ロジック (Dirty Rectangle) の再実装**
    - Pythonレベルのループを排除し、`PIL.ImageChops` 等の高速な手法を用いて更新領域を特定する。
- [ ] **タスク 3.2: pigpiod 通信のバッチ化・効率化**
    - 通信回数を減らすためのバッファリングや、冗長なピン制御命令の削減をライブラリ層（`ST7789V`/`DispSpi`）の知見を活かして適用する。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 3' (Protocol in workflow.md)**

## フェーズ 4: 最終検証と品質確認
- [ ] **タスク 4.1: 改善効果の定量的測定**
    - `tests/test_performance.py` を用いて、フェーズ1の基準値と比較し、改善目標が達成されているか確認する。
- [ ] **タスク 4.2: 挙動の一致確認**
    - 目視および既存の自動テストにより、`roboface2.py` と全く同じ挙動（表情変化、視線移動）が維持されているか確認する。
- [ ] **タスク 4.3: デバッグコードの整理とクリーンアップ**
    - 調査用の `print` 文などを削除し、製品品質のコードに整える。
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 4' (Protocol in workflow.md)**
