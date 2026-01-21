# LCD Check Subcommand Implementation Report

## Overview
`samples/lcd_check.py` のロジックを `pi0disp lcd-check` サブコマンドとして統合しました。

## Implemented Features
- **`lcd-check` サブコマンド**:
    - `invert` と `bgr` の全組み合わせ（4通り）を順次テスト。
    - 画面上に現在の設定値を描画し、視覚的な確認を容易に。
- **対話型ウィザード (`--wizard`)**:
    - リアルタイム調整機能: `a-d`(向き), `i`(反転), `g`(BGR), `hjkl`(位置微調整) キーで画面を見ながら直感的に設定。
    - 残像防止: 設定変更時にフレームバッファキャッシュを強制クリア。
    - 判定結果を `pi0disp.toml` に自動保存する機能を搭載（`tomlkit` によるコメント維持）。
- **柔軟なオプション**:
    - `--rotation`: 任意の回転角でテスト可能。
    - `--invert` / `--bgr`: 特定の設定の個別検証。
    - `--wait`: 指定秒数での自動切り替え。
- **テストパターン描画ユーティリティ**:
    - `src/pi0disp/utils/lcd_test_pattern.py` として抽出し、メンテナンス性を向上。
    - 設定判定ロジックを分離し、TDD で品質を担保。

## Verification Results

### Automated Tests
`tests/test_23_lcd_check_cmd.py` を実装し、以下の内容を自動検証しました。
- コマンドの正常終了。
- オプションによるテスト回数の変化（フィルタリング）。
- 描画された画像のピクセル値検証（RGB各色が正しい位置に描画されているか）。

**Test Execution Log:**
```
tests/test_23_lcd_check_cmd.py::test_lcd_check_basic PASSED
tests/test_23_lcd_check_cmd.py::test_lcd_check_wait PASSED
tests/test_23_lcd_check_cmd.py::test_lcd_check_filter_invert PASSED
tests/test_23_lcd_check_cmd.py::test_lcd_check_pattern_content PASSED
```

### Static Analysis
`mise run lint` を実行し、以下のツールでエラーがないことを確認済み。
- `ruff` (Format & Check)
- `basedpyright`
- `mypy`

## Conclusion
本トラックの実装により、ユーザーは `pi0disp` インストール直後に最適なディスプレイ設定を容易に特定できるようになりました。
また、キャプチャベースの自動テストを導入したことで、物理デバイスなしでも描画ロジックの正確性を維持できる体制を構築しました。
