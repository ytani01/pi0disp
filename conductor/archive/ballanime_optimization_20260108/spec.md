# Specification - ballanime_optimization_20260108

## Overview
`src/pi0disp/commands/ballanime.py` をリファクタリングし、ドライバの最適化機能を活用した「簡略版」と、アプリケーション側で極限まで最適化を行う「高速版」の 2 つのモードを実装する。これにより、実装の複雑さとパフォーマンスのトレードオフを定量的に比較可能にする。

## Functional Requirements
1.  **モード切り替えオプションの追加**:
    - `pi0disp ballanime` に `--mode [simple|fast]` オプションを追加する。
2.  **`simple` モードの実装**:
    - アプリケーション側の `RegionOptimizer` や複雑な境界計算ロジップを削除する。
    - ドライバの `lcd.display(image)` による自動差分検知（Dirty Rectangle）のみに依存し、コードを大幅に簡略化する。
3.  **`fast` モードの実装**:
    - 従来の `display_region` による手動更新を維持しつつ、背景キャッシュなどの最適化パターンを適用する。
    - ドライバ側の画像比較（ImageChops）のコストさえも削減することを目的とする。
4.  **共通の物理・描画ロジック**:
    - 比較の公平性を保つため、ボールの挙動や背景、HUD（FPS表示）などの見た目は両モードで共通とする。
5.  **パフォーマンス計測環境の提供**:
    - `tests/test_performance.py` などを拡張し、`simple` と `fast` のそれぞれの CPU 負荷、メモリ使用率、実測 FPS を自動で計測・比較できるようにする。

## Non-Functional Requirements
- **可読性**: `simple` モードのコードは、新規ユーザーが「このドライバの正しい使い方」を学ぶための手本となるような簡潔さを目指す。
- **後方互換性**: 既存のオプション（`--fps`, `--num-balls` 等）は引き続き利用可能とする。

## Acceptance Criteria
- `pi0disp ballanime --mode simple` および `fast` が正しく動作すること。
- テストスクリプトにより、両モードのパフォーマンス統計が取得可能であること。
- `simple` モードのコードから、不要な領域計算ロジックが排除されていること。

## Out of Scope
- ボールの物理演算エンジンの根本的な変更（今回は表示・更新ロジックの比較に絞る）。
