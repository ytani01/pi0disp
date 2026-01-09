# Track: `ballanime` の改造と性能評価（複数最適化モードの実装）

## フェーズ 1: 基盤のリファクタリングと最適化準備 [checkpoint: 240137c]
### タスク 1.1: `RegionOptimizer` の復元とテスト
- [x] テスト: `tests/test_performance_core.py` に `RegionOptimizer` のマージロジックを網羅するテストを追加する。 [3f2fd33]
- [x] 実装: `src/pi0disp/utils/performance_core.py` に `RegionOptimizer` を復元する。 [3f2fd33]
- [x] 検証: print文やログを用いて、矩形のマージが期待通りに行われているか（重なりがある場合、ない場合など）を実走データで確認する。 [3f2fd33]

### タスク 1.2: `Ball` クラスの `CircleSprite` への移行
- [x] テスト: `tests/test_ballanime_refactor.py` を作成。`Ball` が `CircleSprite` の `dirty_region` 算出ロジックを正しく利用できているか検証する。 [57755d4]
- [x] 実装: `Ball` クラスを `CircleSprite` 継承にリファクタリングする。 [57755d4]
- [x] 検証: デバッグログを出力し、ボールの移動に伴って `dirty_region` が漏れなく算出されているかを事実確認する。 [57755d4]

- [x] Task: Conductor - User Manual Verification '基盤のリファクタリングと最適化準備' (Protocol in workflow.md) [240137c]

## フェーズ 2: `simple` および `optimized` モードの実装 [checkpoint: 1b731a8]
### タスク 2.1: `--mode` オプションの導入と `simple` モードの分離
- [x] テスト: `tests/test_ballanime_cmd.py` で `--mode` オプションのパースと、各モードへの分岐が正しく行われることをテストする。 [b71a854]
- [x] 実装: `--mode` オプションを追加し、既存ロジックを `simple` モードとして隔離する。 [b71a854]
- [x] 検証: 実際にコマンドを叩き、`simple` モードが従来の挙動（全画面更新）を維持していることをログで確認する。 [b71a854]

### タスク 2.2: `optimized` モードの実装
- [x] テスト: モックを用いて、`display_region` が `RegionOptimizer` で算出された矩形に対してのみ呼び出されているかを厳密にテストする。 [ccf5f13]
- [x] 実装: `Sprite` と `RegionOptimizer` を連携させた `optimized` モードを実装する。 [ccf5f13]
- [x] 検証: デバッグモードで「更新された矩形数」をカウントし、期待通りに転送回数が削減されているかを数値で確認する。 [ccf5f13]

- [x] Task: Conductor - User Manual Verification 'simple および optimized モードの実装' (Protocol in workflow.md) [1b731a8]

## フェーズ 3: `cairo` および `cairo-optimized` モードの実装
### タスク 3.1: `Cairo` 描画エンジンの導入
- [x] テスト: `tests/test_cairo_render.py` で、Cairoを用いて描画されたイメージのアルファチャンネルやアンチエイリアス状態を検証する。 [6acd082]
- [x] 実装: `ballanime` に `cairo` モードを実装する。 [6acd082]
- [x] 検証: 拡大表示等を行い、エッジが滑らかになっていることを視覚的に（またはピクセルデータで）事実確認する。 [6acd082]

### タスク 3.2: `cairo-optimized` モードの実装
- [x] テスト: Cairoでの部分描画（`clip`機能など）と、`RegionOptimizer` による送信領域が一致していることをテストする。 [cd90d39]
- [x] 実装: `cairo-optimized` モードを実装する。 [cd90d39]
- [x] 検証: ログを用いて、描画負荷（Cairo処理時間）と転送負荷の両方がバランスよく制御されているかを確認する。 [cd90d39]

- [x] Task: Conductor - User Manual Verification 'cairo および cairo-optimized モードの実装' (Protocol in workflow.md)

## フェーズ 4: ベンチマーク強化とレポート生成
### タスク 4.1: ベンチマーク出力の強化
- [x] テスト: `ballanime` コマンドで測定条件が表示されることを確認。
- [x] 実装: `BenchmarkTracker` 出力を拡張し、モード、ボール数、FPS、SPI速度の表示を追加。
- [x] 検証: 実際のターミナル出力で条件が明示されていることを事実確認。

### タスク 4.2: `ballanime-report.md` の自動生成
- [x] テスト: ファイルが存在しない場合に新規作成され、存在する場合に追記されることを確認。
- [x] 実装: Markdownテーブル形式でのレポート自動生成機能を実装。
- [x] 検証: `ballanime-report.md` が正しく生成され、内容が妥当であることを確認。

- [x] Task: Conductor - User Manual Verification 'ベンチマーク強化とレポート生成' (Protocol in workflow.md)
