# Specification: roboface_critical_bug_fixes

## Overview
`samples/roboface.py` に対するコードレビューで指摘された致命的な不具合を修正する。具体的には、不正データ投入時の無限ループを防止し、将来的な拡張を見据えたスレッドセーフな内部構造（排他制御）を導入することで、システムの堅牢性を向上させる。

## Functional Requirements
- **コマンド処理のバグ修正 (無限ループ防止)**:
    - `RfAnimationEngine.run` 内で、キューから取得したデータが文字列以外の場合でも `pending_expr` を確実に `None` にリセットする。
    - 不正なデータ（int等）が検出された際は、`ERROR` レベルでログを出力し、次のキューの処理へ進む。
- **スレッドセーフ化 (防衛的プログラミング)**:
    - `RfUpdater` クラスに `threading.Lock` を導入する。
    - アニメーションの基準値設定 (`start_change`) と状態更新 (`update`) を同一のロックで保護し、データの整合性を保証する。

## Non-Functional Requirements
- **低オーバーヘッド**: Lock の使用による描画 FPS への影響を最小限に抑える。
- **既存機能の維持**: 修正後も `RandomMode` や `InteractiveMode` の動作、およびアニメーションの滑らかさが損なわれていないことを保証する。

## Acceptance Criteria
- [ ] 不正なオブジェクト（例：`engine.queue.put(123)`）を投入した際、エラーログが出力され、かつその後の正常な表情コマンドが問題なく処理されること。
- [ ] `RfUpdater` 内でロックが適切に使用されており、複数スレッドからの同時アクセスに対してデータの一貫性が保たれる構造になっていること。
- [ ] 既存の自動テスト（`tests/test_roboface_thread.py`, `tests/test_roboface_integration.py` 等）がすべてパスすること。

## Out of Scope
- ポーリング効率の最適化や定数化などの「クリーンアップ」作業（今回はバグ修正に集中する）。
