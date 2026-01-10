# Plan: `plan.md`

## 開発原則: 憶測厳禁
1. 推測厳禁。事実に基づき根本原因を突き止める。
2. `--capture-interval` で取得した連続キャプチャを詳細に分析し、表示崩れの「発生タイミング」と「Dirty Rectangle の範囲」の相関を事実として確認する。
3. `simple` モードの結果を正解とし、それと一致しないピクセルが発生するロジック上の欠陥を特定する。

## Phase 1: Capture Feature and Fact Finding (Red Phase) [checkpoint: bd2d048]
- [x] Task: `src/pi0disp/commands/ballanime.py` に `--capture-interval` (-C) オプションを追加し、`_loop` 内で指定秒数おきに `frame_image` を保存する機能を実装する。 (3091bfb)
- [x] Task: `optimized` モードで `ball-speed` 100、10秒間のベンチマークを実行し、1秒ごとのキャプチャ画像を取得して、表示崩れの具体的な事実（残像や欠け）を記録する。 (bd2d048)
- [x] Task: `cairo-optimized` モードでも同様にキャプチャを取得し、現象の共通点・相違点を事実として特定する。 (bd2d048)
- [x] Task: Conductor - User Manual Verification 'Phase 1: Capture Feature and Fact Finding' (Protocol in workflow.md)

## Phase 2: Root Cause Analysis and Implementation (Green Phase) [checkpoint: 2e49c82]
- [x] Task: キャプチャ画像とログを照らし合わせ、Dirty Rectangle が「前フレームの描画（特にFPSテキスト）」を正しくカバーしきれていない、あるいは背景復元の順序が不適切である等の根本原因を特定する。 (2e49c82)
- [x] Task: 特定した原因に基づき、描画フローおよび Dirty Rectangle の生成ロジックを修正する。 (3c8df55)
    - 修正方針: **FPS表示領域を全フレームで常にDirty領域として扱う**ことで、残像と欠損を完全に排除する。
    - 具体的な範囲: `(0, 0, 200, 50)` 程度の十分な広さを確保する。
- [x] Task: 修正後、再度 `--capture-interval` を用いてキャプチャを取得し、全フレームで表示が正常であることを事実として確認する。 (2e49c82)
- [x] Task: Conductor - User Manual Verification 'Phase 2: Root Cause Analysis and Implementation' (Protocol in workflow.md)

## Phase 3: Quality Gate and Finalization
- [~] Task: `uv run pytest` を実行し、既存のテストおよびリンター（lint）に合格することを確認する。
- [ ] Task: キャプチャ機能を（必要なら）デバッグフラグとして整理し、最終的なコードを提出する。
- [ ] Task: 調査に使用したスクリプトおよびキャプチャ画像を削除する。
- [ ] Task: Conductor - User Manual Verification 'Phase 3: Quality Gate and Finalization' (Protocol in workflow.md)
