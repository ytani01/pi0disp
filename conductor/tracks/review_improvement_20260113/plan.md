# plan.md - アニメーション精度とパフォーマンスの改善計画

## Phase 1: 事実確認とベンチマーク (Red Phase) [checkpoint: d40c925]
現状の課題を数値と画像で「事実」として捉え、修正前の基準を確立します。

- [x] **Task 1.1: パフォーマンス計測テストの作成**
    - `RfRenderer.render_parts` の実行時間を計測し、背景キャッシュがない状態の基準値を記録するテストを記述。
- [x] **Task 1.2: FPS依存の視線移動を検証するテストの作成**
    - 異なるFPS設定（例: 10fps vs 30fps）で一定時間経過後の `current_x` を比較し、差異が出る（不具合）ことを確認するテストを記述。
- [x] **Task 1.3: タイミング誤差を検証するテストの作成**
    - 長時間（100フレーム分等）のループを実行し、目標時間と実際の終了時間の乖離を計測するテストを記述。
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)