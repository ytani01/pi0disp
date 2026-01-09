# Implementation Plan - `performance_core_refactor_20260109`

## フェーズ 1: 現状分析とスリム化設計 [checkpoint: 5fbd982]
- [x] **タスク 1.1: 現在の `performance_core.py` と `sprite.py`, `st7789v.py` の依存関係・重複箇所の詳細分析** (8dd80ae)
- [x] **タスク 1.2: 新しい API インターフェースの定義と、削除対象コードのリストアップ** (3e909d0)
- [x] **Task: Conductor - User Manual Verification 'フェーズ 1' (Protocol in workflow.md)** (3e909d0)

## フェーズ 2: コアリファクタリングの実施 [checkpoint: 84439c2]
- [x] **タスク 2.1: `performance_core.py` のコード刷新（不要なクラス・メソッドの削除と API 再構成）** (4f8c06d)
- [x] **タスク 2.2: ユニットテストの作成と実行（TDDサイクル）** (c32906e)
- [x] **Task: Conductor - User Manual Verification 'フェーズ 2' (Protocol in workflow.md)** (c32906e)

## フェーズ 3: マニュアル作成とサンプルコード実装 [checkpoint: a636984]
- [ ] **タスク 3.1: リファレンスマニュアルの執筆（Markdown）**
- [ ] **タスク 3.2: 刷新された API を使用した、わかりやすいサンプルコードの作成**
- [ ] **タスク 3.3: 既存のサンプル（もしあれば）の調整または新サンプルへの置き換え確認**
- [ ] **Task: Conductor - User Manual Verification 'フェーズ 3' (Protocol in workflow.md)**

## フェーズ 4: 最終確認 [checkpoint: ]
- [x] **タスク 4.1: ドキュメントとコードの整合性チェック** (c32906e)
- [x] **タスク 4.2: 統合テストおよびパフォーマンス検証の実行** (c32906e)
- [x] **Task: Conductor - User Manual Verification 'フェーズ 4' (Protocol in workflow.md)** (c32906e)