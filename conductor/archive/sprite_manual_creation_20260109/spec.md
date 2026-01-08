# Track Specification: sprite_manual_creation_20260109

## Overview
`src/pi0disp/utils/sprite.py` に含まれる `Sprite` システムの利用マニュアル `docs/sprite-manual.md` を作成する。開発者が効率的にアニメーションや動的UIを実装できるように、設計思想から具体的な実装手順までを網羅する。

## Functional Requirements
- **マニュアルの作成**: `docs/sprite-manual.md` を新規作成する。
- **構成内容**:
    - **設計思想**: なぜ `Sprite` が抽象クラスなのか、どのような利点があるかの解説。
    - **Dirty Rectangle 管理**: `get_dirty_region()` を用いた差分更新の仕組みと、`record_current_bbox()` を呼ぶタイミングについての技術解説。
    - **基本コンポーネント**: `Sprite` 基底クラスおよび `CircleSprite` のプロパティ・メソッドの紹介。
    - **実装ガイド**: `Sprite` を継承してカスタム描画（矩形、画像等）を行うためのコードテンプレートの提供。
- **サンプルコード**: 各解説セクションにおいて、要点を理解するための簡潔なコードスニペット（断片）を記載する。

## Non-Functional Requirements
- **可読性**: 専門的な用語を使いつつも、具体的な手順がイメージしやすい構成にする。
- **正確性**: 最新のリファクタリング（`__slots__` の導入や `CircleSprite` の追加）の内容を正確に反映する。

## Acceptance Criteria
- `docs/sprite-manual.md` が存在し、上記の内容が過不足なく記述されていること。
- `Sprite` を使って新しい要素を作ろうとする開発者が、このマニュアルだけで実装を開始できること。

## Out of Scope
- マニュアル以外のコード（`src/` や `tests/`）の変更。
- 外部への公開用ドキュメントサイト（GitHub Pages 等）の構築。
