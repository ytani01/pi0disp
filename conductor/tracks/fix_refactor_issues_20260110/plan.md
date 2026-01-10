# Plan: `plan.md`

## 開発原則: 憶測厳禁
1. 推測厳禁。事実に基づき根本原因を突き止める。
2. デバッグログ、print、およびキャプチャ画像を活用し、表示崩れや座標計算の事実を確認する。
3. 可能な限り自動テスト（TDD）を実施する。

## Phase 1: Analysis and Red Phase (Failing Tests)
- [x] Task: `tests/test_sprite_refactor.py` において、`get_dirty_region()` が `(x, y, w, h)` 形式を返すことを期待するテスト（現状は失敗するはず）を追加する
- [~] Task: `tests/test_ballanime_cmd.py` または新規テストで、ベンチマークレポート出力に `Mem (pig)` 列が含まれることを検証する失敗テストを作成する
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Analysis and Red Phase' (Protocol in workflow.md)

## Phase 2: Implementation and Optimization (Green Phase)
- [ ] Task: `src/pi0disp/utils/sprite.py` の `get_dirty_region()` を修正し、期待される `(x, y, w, h)` 形式を返すようにする
- [ ] Task: `src/pi0disp/commands/ballanime.py` の Cairo/PIL 変換ロジックを NumPy スライス操作（`data[:, :, [2, 1, 0, 3]]` 等）に置き換えて最適化する
- [ ] Task: `src/pi0disp/commands/ballanime.py` の `optimized` モード等の描画ループを整理し、`ImageDraw` オブジェクトの冗長な作成を削減する
- [ ] Task: `src/pi0disp/disp/st7789v.py` の `display()` メソッドを、毎フレームの `image.copy()` ではなく差分パッチ適用方式に変更する
- [ ] Task: `ballanime` コマンドのレポート出力処理を修正し、ヘッダーとデータ行の両方に `Mem (pig)` を追加する
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation and Optimization' (Protocol in workflow.md)

## Phase 3: Verification, Documentation, and Quality Gate
- [ ] Task: `ballanime` の各最適化モードを実行し、キャプチャ画像（`/tmp/debug_render.png` 等）を出力・確認して描画の正常性を事実として確認する
- [ ] Task: 修正内容に合わせて `docs/sprite-manual.md` および `docs/performance_core_manual.md` の記述を更新する
- [ ] Task: `mise run test` を実行し、全テストのパスおよびリンター（lint）の合格を確認する
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Verification, Documentation, and Quality Gate' (Protocol in workflow.md)
