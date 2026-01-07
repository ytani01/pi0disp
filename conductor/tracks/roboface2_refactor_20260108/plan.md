# Implementation Plan - roboface2 クラス構造のリファクタリング

## Phase 1: 基礎構造と定数の整理 (Rf命名規則の導入)
- [x] 設定クラス `RfConfig` (旧 FaceConfig) の拡張
    - `LAYOUT`, `COLORS`, `ANIMATION` 定数を `RfConfig` 内の属性またはサブクラスに集約する。
- [x] 状態クラス群の改称と整理
    - `BrowState` -> `RfBrowState`, `EyeState` -> `RfEyeState` 等へのリネーム。
- [x] インターフェース定義の確認
    - `DisplayBase` のメソッド名の見直し（より汎用的な命名へ）。
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: コアロジックの再構築 (RobotFace と Renderer) [checkpoint: 2c8b068]
- [x] `RfRenderer` (旧 DrawFace) のリファクタリング (2c8b068)
    - `RobotFace` から独立させ、`RfState` と `PIL.Image` を受け取って描画する純粋な描画機能に特化させる。
- [x] `RobotFace` クラスの刷新 (2c8b068)
    - `update()` による自律的なアニメーション管理の実装。
    - `FaceUpdater` の機能を `RobotFace` 内部に統合、またはプライベートな責務として整理。
- [x] `RfParser` (旧 FaceStrParser) のリファクタリング (2c8b068)
    - 文字列から `RfState` への変換ロジックを独立させる。
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md) (2c8b068)

## Phase 3: アプリケーション層の適合と統合テスト [checkpoint: 6e92f95]
- [x] `AppMode` およびその派生クラス (`RandomMode`, `InteractiveMode`) の修正 (6e92f95)
    - 新しい `RobotFace` のインターフェースを使用するように書き換える。
- [x] エントリポイント (`main`) の整理 (6e92f95)
    - `RobotFaceApp` と CLI ロジックの分離を明確にする。
- [x] 動作確認 (6e92f95)
    - `samples/roboface2.py` を実行し、ランダムモード・対話モードが正しく動作することを確認。
- [x] リンティングと型チェックの実行 (6e92f95)
    - `mise run lint` および `mypy` による検証。
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md) (6e92f95)
