# plan.md - アニメーション精度とパフォーマンスの改善計画

## Phase 1: 事実確認とベンチマーク (Red Phase) [checkpoint: d40c925]
現状の課題を数値と画像で「事実」として捉え、修正前の基準を確立します。

- [x] **Task 1.1: パフォーマンス計測テストの作成**
    - `RfRenderer.render_parts` の実行時間を計測し、背景キャッシュがない状態の基準値を記録するテストを記述.
- [x] **Task 1.2: FPS依存の視線移動を検証するテストの作成**
    - 異なるFPS設定（例: 10fps vs 30fps）で一定時間経過後の `current_x` を比較し、差異が出る（不具合）ことを確認するテストを記述.
- [x] **Task 1.3: タイミング誤差を検証するテストの作成**
    - 長時間（100フレーム分等）のループを実行し、目標時間と実際の終了時間の乖離を計測するテストを記述.
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: ロジックの修正と自動テストのパス (Green Phase) [checkpoint: 39da856]
指摘事項を修正し、Phase 1 で作成したテストがパスするようにします.

- [x] **Task 2.1: 背景キャッシュの実装 (RfRenderer)**
    - パディング済みの背景画像を保持するキャッシュ変数を導入し、`render_parts` の負荷を低減する.
- [x] **Task 2.2: 時間ベースの視線補間への移行 (RfAnimationEngine)**
    - `interval` を考慮した補間計算式に更新し、FPSに依存しない移動速度を実現する.
- [x] **Task 2.3: ドリフト補償付きタイミングループの実装 (Random/InteractiveMode)**
    - `next_tick` を管理するループ構造に変更し、タイミング精度を向上させる.
- [x] **Task 2.4: 自動テストによる一括検証**
    - Phase 1 のテストをすべてパスさせ、改善効果を数値で確認する.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: 品質確保とリファクタリング (Refactor Phase) [checkpoint: c201564]
コードを整理し、最終的な品質基準を満たしていることを確認します.

- [x] **Task 3.1: テストコードの整理とカバレッジ確認**
    - 使用した一時ファイルやデバッグログを整理し、カバレッジが 80% 以上であることを確認.
- [x] **Task 3.2: リンターと型チェックの実行**
    - `uv run ruff check .` を実行し、静的解析エラーを解消する.
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)