# Plan: `plan.md`

## 開発原則: 憶測厳禁
1. 推測厳禁。事実に基づき根本原因を突き止める。
2. キャプチャ画像と画像解析（ピクセルチェック）を組み合わせた自動テストを作成し、表示欠損を事実として検出する。
3. `optimized` および `cairo-optimized` 各モードの描画パイプラインを詳細に分析する。

## Phase 1: Automated Reproduction and Fact Finding (Red Phase)
- [x] Task: 描画結果を検証するための自動スクリプト `tests/verify_fps_glitch.py` を作成する。 (cfa790e)
- [x] Task: 作成したスクリプトを実行し、現在のコードで FPS 表示が欠損する事実をテスト失敗として確認する。 (cfa790e)
- [ ] Task: Conductor - User Manual Verification 'Phase 1: Automated Reproduction and Fact Finding' (Protocol in workflow.md)

## Phase 2: Implementation and Fix (Green Phase)

- [x] Task: `src/pi0disp/commands/ballanime.py` の `optimized` モードにおける Dirty Rectangle の判定と `fps_area_overlap` のロジックを再点検し、漏れなく再描画が行われるように修正する。 (057396f)

- [x] Task: `cairo-optimized` モードに対しても同様の修正を適用する。 (057396f)

- [x] Task: `tests/verify_fps_glitch.py` を再実行し、ボール重なり時も FPS 表示が維持され、テストがパスすることを事実として確認する。 (057396f)


- [ ] Task: Conductor - User Manual Verification 'Phase 2: Implementation and Fix' (Protocol in workflow.md)

## Phase 3: Quality Gate and Cleanup

- [x] Task: 既存の全てのテスト (`mise run test`) を実行し、デグレがないことを確認する。 (3ee8001)

- [x] Task: `mise run lint` を実行し、静的解析エラーがないことを確認する。 (3ee8001)

- [x] Task: 今回作成した検証スクリプトを必要に応じて永続的なテストケースとして整備するか、アーカイブする。 (3ee8001)


- [ ] Task: Conductor - User Manual Verification 'Phase 3: Quality Gate and Cleanup' (Protocol in workflow.md)
