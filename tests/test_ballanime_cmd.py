# -*- coding: utf-8 -*-
from click.testing import CliRunner

from pi0disp.commands.ballanime import ballanime


def test_ballanime_mode_option():
    runner = CliRunner()
    # 実行せずにヘルプだけ確認（オプションが存在するか）
    result = runner.invoke(ballanime, ["--help"])
    assert result.exit_code == 0
    assert "--mode" in result.output
    assert "simple" in result.output
    assert "optimized" in result.output
    assert "cairo" in result.output


# 実際の分岐テストは、内部関数をパッチして行うのが望ましいが、
# まずはオプションのパースが通ることを確認する。
