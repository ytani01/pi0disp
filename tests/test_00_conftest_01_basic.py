# tests/test_00_conftest.py
#
# `conftest.py` の動作確認用テストプログラム
#
# `cli_runner`: conftest.pyで定義されたフィクスチャー
#
import pytest

KEY_EOF = "\x04"


class TestBasicCommands:
    """基本的なコマンドのテスト。"""

    @pytest.mark.parametrize(
        "command, expected",
        [
            (["echo", "Hello"], "Hello\n"),
            (["echo", "-n", "No newline"], "No newline"),
        ],
    )
    def test_echo(self, cli_runner, command, expected):
        """`echo` コマンドの出力をテストします。"""
        cli_runner.test_command(command, e_stdout=expected)


class TestAdvancedCommands:
    """入力やパイプなど、より高度な機能のテスト。"""

    @pytest.mark.parametrize(
        "input_name, expected",
        [
            ("World\n", ["Hello World", "Hello", "World"]),
            ("Alice\n", ["Hello Alice"]),
            ("\n", "Hello"),
            (KEY_EOF, "Hello"),
        ],
    )
    def test_command_with_input(self, cli_runner, input_name, expected):
        """標準入力を使用するコマンドをテストします。"""
        cmdline = ["python3", "-c", "name = input(); print('Hello ' + name)"]

        print("\n* test_command(...)")
        cli_runner.test_command(
            cmdline, input_data=input_name, e_stdout=expected, e_ret=0
        )

        inout = {"in": input_name, "out": expected}
        print("* test_interactive(...)")
        print(f"* inout={inout}")
        cli_runner.test_interactive(
            cmdline, in_out=inout, terminate_flag=False
        )
