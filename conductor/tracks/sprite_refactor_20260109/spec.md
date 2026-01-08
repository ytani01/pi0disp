# Track Specification: sprite_refactor_20260109

## Overview
`report.md` の調査結果に基づき、`src/pi0disp/utils/sprite.py` をリファクタリングしてパフォーマンス向上と機能拡張を行う。属性アクセスの高速化、再描画領域計算の最適化、および円形スプライトへの対応を実施する。

## Functional Requirements
- **属性アクセスの高速化**: `Sprite` クラスおよびその派生クラスに `__slots__` を導入する。
- **Dirty Region 計算の最適化**:
    - 座標やサイズに変更があった場合のみ `dirty` と判定する仕組みを導入。
    - `get_dirty_region()` は、変更がない場合には計算をスキップして `None` を返すようにする。
- **CircleSprite の追加**:
    - `Sprite` を継承した `CircleSprite` クラスを実装する。
    - 中心座標 (`cx`, `cy`) と半径 (`radius`) で初期化・操作できるインターフェースを提供する。
    - `bbox` プロパティなどを適切にオーバーライドし、円形に対応させる。

## Non-Functional Requirements
- **パフォーマンス**: 大量（100個〜）のスプライトを生成した際でも、属性アクセスや領域計算によるオーバーヘッドを最小限に抑える。
- **後方互換性**: 既存 of `Sprite` の初期化引数 (`x`, `y`, `width`, `height`) とメソッドシグネチャを維持する。

## Acceptance Criteria
- `Sprite` クラスに `__slots__` が導入されていること。
- 座標を動かさない状態で `get_dirty_region()` を呼び出した際、`None` が返されること。
- `CircleSprite` クラスが正しく動作し、中心座標と半径から期待される `bbox` が取得できること。
- 新しく作成するユニットテストがすべて合格すること。

## Out of Scope
- `ballanime.py` などの既存コマンドへの即時適用（本トラックはライブラリの改善までとする）。
- アニメーションエンジンの追加機能（当たり判定など）。
