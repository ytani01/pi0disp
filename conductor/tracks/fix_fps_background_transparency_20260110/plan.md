# Plan: `plan.md`

## 開発原則: 憶測厳禁
1. 推測厳禁。事実に基づき根本原因を突き止める。
2. 描画順序と `frame_image.paste` の呼び出し箇所をコードレベルで詳細に特定する。
3. キャプチャ画像を用いて、ボールが欠ける「瞬間」の事実を記録・検証する。

## Phase 1: Fact Finding and Analysis (Red Phase)
- [x] Task: `ballanime` の `optimized` モードを実行し、ボールが FPS エリアを通過する際のキャプチャ画像を取得して、ボールが背景パッチで上書きされている事実を確認する (0cb02a7)
- [x] Task: `src/pi0disp/commands/ballanime.py` の `_loop` 内の描画フローを分析し、`text_patch` の `paste` 処理がボールの `draw` 処理の後に実行されていることを事実として特定する (0cb02a7)
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Fact Finding and Analysis' (Protocol in workflow.md)

## Phase 2: Fix Implementation (Green Phase)
- [ ] Task: `optimized` モードにおいて、FPS エリアの背景復元を他の Dirty Rectangle と同様に「描画の最初（ステップ1）」に移動し、テキスト描画直前の破壊的な `paste` を削除する
- [ ] Task: `cairo-optimized` モードに対しても同様の修正（背景復元の統合と冗長なパッチ上書きの削除）を適用する
- [ ] Task: 修正後、`ball-speed` 100 で実行し、ボールが FPS テキストの下を透過して（あるいは正しく重なって）スムーズに通過することをキャプチャ画像で事実として確認する
- [ ] Task: Conductor - User Manual Verification 'Phase 2: Fix Implementation' (Protocol in workflow.md)

## Phase 3: Final Verification and Cleanup
- [ ] Task: `mise run test` を実行し、既存のテストおよびリンター（lint）に合格することを確認する
- [ ] Task: 修正内容を反映した最終的な `ballanime-report.md` への追記を確認する
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Final Verification and Cleanup' (Protocol in workflow.md)
