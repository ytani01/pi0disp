# Specification: `spec.md`

## Overview
`ballanime` の `optimized` および `cairo-optimized` モードにおいて、FPS表示エリアの背景が透過しなくなり（背景パッチがボールを隠してしまい）、`simple` モードと見え方が異なっている問題を修正します。

## Functional Requirements
- **描画順序の適正化**: FPSテキスト描画時の背景クリア処理（`text_patch` の貼り付け）が、ボールの描画を上書きしないように順序を整理します。
- **`simple` モードとの外観一致**: `optimized` モードであっても、FPSテキストの背景には常に最新のボールの状態および背景グラデーションが見えるようにします。

## Non-Functional Requirements
- **実装原則（憶測厳禁）**: 描画レイヤーの重なり順をコードから正確に把握し、キャプチャ画像を用いて事実に基づいた修正を行います。
- **パフォーマンスの維持**: 修正により Dirty Rectangle 最適化の利点が失われないように（不必要な全画面再描画を避ける）配慮します。

## Acceptance Criteria
- [ ] ボールが画面左上の FPS 表示エリアを通過する際、ボールがテキストの下（または上）に正しく描画され、矩形の背景パッチによって遮られないこと。
- [ ] `optimized` および `cairo-optimized` モードにおいて、FPS表示の外観が `simple` モードと同一であることを事実として確認すること。
- [ ] 静的解析（`mise run lint`）および既存テストをパスすること。

## Out of Scope
- FPS表示以外のUI改善。
- `simple` モード自体のロジック変更。
