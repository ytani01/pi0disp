# plan.md

## Phase 1: 事実確認と失敗するテストの作成 (Red Phase) [checkpoint: da709c6]
不具合の挙動をデバッグログやテストで「事実」として捉え、修正前の状態を確定させます。

- [x] **Task 1.1: `duration=0.0` の不具合を再現するテストの作成** (da709c6)
    - `RfUpdater` に `duration=0.0` を渡した際、即座に変化率が 1.0 にならないことを確認するテストを記述。
- [x] **Task 1.2: 背景色（文字列指定）の不具合を再現するテストの作成** (da709c6)
    - `render_parts` に `"white"` などの文字列を渡し、生成された画像の隅のピクセルが黒 `(0, 0, 0)` になっている（不具合）ことを検証するテストを記述。
- [x] **Task 1.3: 背景キャッシュの不備を再現するテストの作成** (da709c6)
    - 1度描画した後に `bg_color` を変えて再度描画し、画像が更新されない（古い色のまま）ことを検証するテストを記述。
- [x] **Task 1.4: 現状の挙動の証拠保存 (Debug Artifacts)** (da709c6)
    - テスト実行時に不具合状態の画像をファイルとして保存し、目視でも「事実」を確認可能にする。
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: 不具合の修正と自動テストのパス (Green Phase) [checkpoint: 57c2471]
特定した根本原因を修正し、自動テストがすべてパスする状態にします。

- [x] **Task 2.1: `RfUpdater.start_change` の判定ロジック修正 (L552)** (57c2471)
    - `if not duration:` を `if duration is None:` に修正。
- [x] **Task 2.2: パディング色の継承ロジック修正 (L740, L938)** (57c2471)
    - `pad_color` の三項演算子を削除し、`bg_color` を直接渡すよう修正.
- [x] **Task 2.3: `RfRenderer` のキャッシュ無効化実装 (L924)** (57c2471)
    - `_cached_bg_color` を導入し、色変更を検知してキャッシュを再生成するロジックを追加.
- [x] **Task 2.4: 自動テストによる一括検証** (57c2471)
    - Phase 1 で作成したテストがすべてパスすることを確認.
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: 品質向上とリファクタリング (Refactor Phase)
テストの保護下でコードを整理し、最終的な品質を確認します。

- [x] **Task 3.1: テストコードの整理と検証項目の強化** (57c2471)
    - テスト用の画像保存ロジックを整理し、境界条件（非常に短い duration など）のテストを追加。
- [x] **Task 3.2: リンターと型チェックの実行** (57c2471)
    - `ruff check` を実行し、コード品質を確保。
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)
