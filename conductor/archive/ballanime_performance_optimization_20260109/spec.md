# Track: `ballanime` の改造と性能評価（複数最適化モードの実装）

## 概要 (Overview)
前回の調査結果（`report.md`）に基づき、`ballanime` コマンドに複数の最適化モードを実装します。ドライバ任せの自動更新（`simple`）に加え、`Sprite` や `RegionOptimizer` を活用した「アプリケーション主導型最適化」、および `Cairo` による高品質描画モードを導入し、Raspberry Pi Zero 2W 等の非力な環境におけるパフォーマンスと描画品質の違いを定量的に評価します。

## 機能要件 (Functional Requirements)
- **複数モードの実装 (`--mode` オプション)**:
    - `simple` (デフォルト): 現在の実装。初心者が最も理解しやすいコードを維持する（ベースライン）。
    - `optimized`: `CircleSprite` を継承したクラスへのリファクタリングを行い、`RegionOptimizer` による領域統合と `display_region` を用いた差分更新を行う。
    - `cairo`: `Cairo` ライブラリを使用し、アンチエイリアスの効いた滑らかな描画を行う。
    - `cairo-optimized`: `Cairo` による描画と `RegionOptimizer` による領域最適化を組み合わせる。
- **ベンチマーク機能の強化 (`--benchmark`)**:
    - 測定開始前に、ターゲットFPS、ボール数、ボール速度、SPIクロック等の「実行条件」を出力する。
    - 測定結果として、平均FPS、CPU負荷（`ballanime` および `pigpiod`）を表示する。
- **パフォーマンス評価レポートの生成**:
    - 測定結果を `ballanime-report.md` としてプロジェクトルートに保存する。
    - 各モード間の性能差（CPU負荷低減率、SPI転送効率）および描画品質の差異をまとめる。
- **ハードウェア対応**:
    - Raspberry Pi Zero 2W での動作を前提とした最適化を行う。

## 非機能要件 (Non-Functional Requirements)
- **コードの可読性**: `simple` モードのコードは、教育的な観点から複雑な最適化を排除した平易な状態を保つ。
- **正確な測定**: `psutil` を使用し、事実に基づいた負荷計測を行う。
- **日本語ドキュメント**: レポートおよびチャットは日本語で作成する。

## 受け入れ基準 (Acceptance Criteria)
- `pi0disp ballanime --mode [simple|optimized|cairo|cairo-optimized]` が正常に動作すること。
- `--benchmark` 実行時に詳細な条件と結果が表示されること。
- プロジェクトルートに `ballanime-report.md` が生成され、各モードの比較結果が記載されていること。
- `Cairo` 使用時に描画が明らかに滑らか（アンチエイリアス有効）になっていること。

## 範囲外 (Out of Scope)
- `ballanime` 以外のサブコマンドへの最適化適用。
- ハードウェア（SPIバス等）自体のクロックアップ。
