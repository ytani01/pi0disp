# 仕様書: コードレビュー指摘事項に基づく改善と修正

## 1. 概要 (Overview)
`review_result.md` で指摘されたバグ修正、パフォーマンス最適化、および一貫性の欠如を解消するためのリファクタリングを実施する。また、変更された API 仕様に合わせて関連ドキュメントを更新し、プロジェクトの品質と保守性を向上させる。

## 2. 機能要件 (Functional Requirements)
- **[重要度: 高] 座標形式の統一 (`src/pi0disp/utils/sprite.py`)**:
    - `Sprite.get_dirty_region()` が返却する形式を `(x0, y0, x1, y1)` から `(x, y, w, h)` に変更する。
- **[重要度: 中] 画像処理の高速化 (`src/pi0disp/commands/ballanime.py`)**:
    - PIL/Cairo 間の変換において `split()` / `merge()` を廃止し、NumPy スライス操作による高速なチャンネル並べ替えを導入する。
- **[重要度: 中] 描画オーバーヘッドの削減 (`src/pi0disp/commands/ballanime.py`)**:
    - 最適化モードにおいて `ImageDraw` オブジェクトの作成回数を最小化し、描画ループを効率化する。
- **[重要度: 中] メモリコピーの最適化 (`src/pi0disp/disp/st7789v.py`)**:
    - `display()` メソッドにおいて、毎フレームの `image.copy()` を避け、差分領域のみをキャッシュに適用する方式に変更する。
- **[重要度: 低] レポート出力の修正 (`src/pi0disp/commands/ballanime.py`)**:
    - ベンチマークレポートのヘッダーとデータ行の不一致を解消する。
- **ドキュメント更新**:
    - `docs/sprite-manual.md` および `docs/performance_core_manual.md` を、修正後の API 仕様に合わせて更新する。

## 3. 非機能要件 (Non-Functional Requirements)
- **パフォーマンス**: 修正により、特に `optimized` および `cairo` 系の描画モードにおいて、現状と同等以上の FPS を維持すること。
- **後方互換性**: `Sprite` クラスの API 変更を伴うため、ドキュメントを確実に更新し、利用側の混乱を防ぐ。
- **憶測厳禁**: 各修正の効果をログやテストで確認し、事実に基づいて実装を完了させる。

## 4. 受け入れ基準 (Acceptance Criteria)
- [ ] すべての自動テスト（既存および新規）がパスすること。
- [ ] `ballanime` コマンドが全モードで期待通り（表示崩れなく）動作すること。
- [ ] `mise run lint` および `mypy` でエラーが発生しないこと。
- [ ] ドキュメント内のコード例と実際の実装が整合していること。

## 5. 範囲外 (Out of Scope)
- `review_result.md` に記載されていない新機能の追加。
- ハードウェア（SPIバス等）自体の仕様変更。
