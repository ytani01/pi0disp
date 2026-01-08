# Track Specification: sprite_utility_investigation_20260109

## Overview
現在 `src/pi0disp/utils/sprite.py` に存在する `Sprite` クラスの存在価値を検証する。特に、既存のアニメーションコマンド（`ballanime` 等）で現在個別に実装されているロジックを `Sprite` クラスで代替できるか、また代替することによるメリット・デメリット（パフォーマンス、保守性）を明らかにし、最終的な推奨アクションを報告する。

## Functional Requirements (調査項目)
- **コード分析**: `sprite.py` の提供機能をリストアップし、`ballanime.py` の `Ball` クラス等との機能差分を特定する。
- **パフォーマンス考察**: `Sprite` クラスの描画方式（Pillowベースなど）が、現在の最適化された描画ロジックに適合するか、オーバーヘッドが発生しないかを技術的に評価する。
- **活用可能性の検討**: `ballanime` 以外の将来的なユースケース（ゲーム、UI要素の動的描画など）における `Sprite` クラスの有効性を評価する。

## Non-Functional Requirements
- 実際のプロダクトコード（`src/` 配下）の変更や削除は本トラックの範囲外とする。
- 調査結果は `conductor/tracks/<track_id>/report.md`（または同様のドキュメント）にまとめる。

## Acceptance Criteria
- `sprite.py` の現状の機能と課題が明文化されていること。
- `ballanime` などの既存コードへの統合案、または削除・放置のいずれかの推奨アクションが示されていること。
- 調査レポートが作成され、成果物として提出されていること。

## Out of Scope
- `sprite.py` に基づく実際のリファクタリング（コードの書き換え）。
- `sprite.py` の削除。
- 新しいスプライトエンジンの実装。
