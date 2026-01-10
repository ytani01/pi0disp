# Plan: `plan.md`

## 開発原則: 憶測厳禁
1. 推測厳禁。事実に基づき根本原因を突き止める。
2. デバッグログ、print、およびキャプチャ画像を活用し、表示崩れや座標計算の事実を確認する。
3. 可能な限り自動テスト（TDD）を実施する。

## Phase 1: Analysis and Reproduction (Red Phase)
- [x] Task: 新しい作業ブランチ `fix-fps-display-glitch` を作成する (8880ed5)
- [ ] Task: `ballanime` の `optimized` モードで `ball-speed` を 100 に設定し、FPS表示が欠ける瞬間のキャプチャ画像を取得して現状を事実として記録する
- [ ] Task: 同様の調査を `cairo-optimized` モードでも実施し、差異や共通点を特定する
- [ ] Task: `src/pi0disp/commands/ballanime.py` の `optimized` モード内の描画・更新ロジックに詳細ログを追加し、FPS描画領域 (`0, 0, 100, 40`) と `RegionOptimizer` が出力する矩形のマージ・上書きプロセスを事実に基いて分析する
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Analysis and Reproduction' (Protocol in workflow.md)

## Phase 2: Implementation (Green Phase)
- [ ] Task: 調査結果に基づき、`src/pi0disp/commands/ballanime.py` 内の Dirty Rectangle 処理（特に FPS 表示領域の保護または再描画順序）を修正する
- [ ] Task: 修正後、`ball-speed` を 100 に設定して各モードでキャプチャ画像を取得し、FPS表示が欠けないことを事実として確認する
- [ ] Task: 必要に応じて `optimized` モードと `cairo-optimized` モードの両方で一貫した修正を適用する
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation' (Protocol in workflow.md)

## Phase 3: Final Verification and Quality Gate
- [ ] Task: 既存の自動テスト (`tests/test_ballanime_*.py`) を実行し、デグレがないことを確認する
- [ ] Task: `mise run lint` を実行し、静的解析エラーがないことを確認する
- [ ] Task: 修正内容を反映したキャプチャ画像を最終エビデンスとして記録する
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Final Verification and Quality Gate' (Protocol in workflow.md)
