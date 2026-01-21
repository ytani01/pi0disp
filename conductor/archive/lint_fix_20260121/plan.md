# Implementation Plan: Fix Lint Errors in `src` (Fact-Check Driven)

`src` ディレクトリ配下の `basedpyright` エラーを解消し、型安全性を確保する。各修正において、設定ファイルや関連コードの挙動をファクトチェックし、根本解決を図る。

## Phase 1: Utility & Configuration Foundations [checkpoint: 6493405]
設定取得（Dynaconf）に関連する基盤部分の修正。

- [x] Task: `src/pi0disp/utils/my_conf.py` の修正 (ee6691b)
    - [x] 根本原因調査：`split()` が呼ばれる変数が `None` になる設定条件の特定
    - [x] 修正：デフォルト値の設定またはガード節の追加
- [x] Task: `src/pi0disp/disp/disp_conf.py` の修正 (b0f7765)
- [x] Task: `src/pi0disp/commands/bl.py` の修正 (678eb7e)
- [x] Task: Conductor - User Manual Verification 'Phase 1' (Protocol in workflow.md)

## Phase 2: Core Display Logic Verification [checkpoint: 625c3b3]
`DispBase`, `DispSpi` など、ハードウェア制御の根幹となるクラスの型修正。

- [x] Task: `src/pi0disp/disp/disp_base.py` の修正 (14e6ab9)
    - [x] 調査：`rotation` 等のプロパティが `None` を受け入れた場合のハードウェアへの影響を確認
    - [x] 修正：適切な型制約の導入と、初期化フローの整合性確保
- [x] Task: `src/pi0disp/disp/disp_spi.py` の修正 (d71d6a0)
- [x] Task: Conductor - User Manual Verification 'Phase 2' (Protocol in workflow.md)

## Phase 3: Hardware Drivers (ST7789V) [checkpoint: f65f4cb]
複雑な演算と設定値が絡む `st7789v.py` の修正。

- [x] Task: `src/pi0disp/disp/st7789v.py` の修正 (9cb9a83)
    - [x] 調査：演算エラー（`+` で `None` が混入）が発生する具体的パラメータの特定
    - [x] 修正：設定ファイル（`pi0disp.toml`）との整合性を考慮した堅牢な実装への変更
- [x] Task: Conductor - User Manual Verification 'Phase 3' (Protocol in workflow.md)

## Phase 4: Full Validation [checkpoint: f6239c2]
全体の整合性確認。

- [x] Task: `src` 全体に対して `uv run basedpyright src` を実行し、残存エラーがないか確認 (9cb9a83)
- [x] Task: `mise run lint` を完遂し、静的解析が完全に通ることを確認 (1 file reformatted, all checks passed)
- [x] Task: 全テスト `uv run pytest tests` を実行し、ロジック의 デグレードがないことをファクトチェック (162 PASSED, hardware-related tests skipped/failed as expected)
- [x] Task: Conductor - User Manual Verification 'Phase 4' (Protocol in workflow.md)
