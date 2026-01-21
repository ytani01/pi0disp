import os
import pty
import select
import subprocess
import time
from typing import Optional

import pytest

TIMEOUT_EXPECT = 25.0
TIMEOUT_CLOSE = 5.0


class InteractiveSession:
    """Interactive session."""

    def __init__(self, master_fd, process):
        """Constractor."""
        self.master_fd = master_fd
        self.process = process
        self.output = ""

    def send_key(self, key: str):
        """Sends a key press to the process."""
        if not key:
            return

        print(f"## key-input: {key!r}")
        os.write(self.master_fd, key.encode())

    def expect(
        self, pattern: str | list[str], timeout: float = TIMEOUT_EXPECT
    ) -> bool:
        """Waits for a pattern to appear in the output."""
        if not pattern:
            return True

        if isinstance(pattern, str):
            pattern = [pattern]
        print(f"### excpect: {pattern!r}")

        start_time = time.time()
        self.output = ""
        while time.time() - start_time < timeout:
            r, _, _ = select.select([self.master_fd], [], [], 0.1)
            if r:
                try:
                    data = os.read(self.master_fd, 1024).decode()
                    self.output += data
                    # print(f"### Current output: \n{self.output}")
                    matched_pattern = []
                    for p in pattern:
                        if p in self.output:
                            matched_pattern.append(p)
                    print(
                        "#### data\n"
                        f"{data!r}\n"
                        "##### matched:"
                        f"{len(matched_pattern)}/{len(pattern)}:"
                        f" {matched_pattern}"
                    )
                    if len(matched_pattern) == len(pattern):
                        # print(f"#### matched all: {pattern!r}")
                        return True

                except UnicodeDecodeError as _e:
                    print(f"{type(_e).__name__}, {_e}")
                    continue

                except OSError as _e:
                    print(f"{type(_e).__name__}, {_e}")
                    break
            time.sleep(0.05)
        return False

    def assert_out(
        self,
        e_stdout: str | list[str] | None = None,
        e_stderr: str | list[str] | None = None,
        timeout: float = TIMEOUT_EXPECT,
    ):
        """Assert output."""
        if e_stdout:
            print("## <stdout>")
            assert self.expect(e_stdout, timeout=timeout)
        if e_stderr:
            print("## <stderr>")
            assert self.expect(e_stderr, timeout=timeout)

    def assert_in_out(
        self,
        in_data: str | list[str],
        out_data: str | list[str],
        timeout: float = TIMEOUT_EXPECT,
    ):
        """Assert interactive in and out."""
        # print(f"in_data={in_data!r}")
        if isinstance(in_data, str):
            in_data = [in_data]

        for _i in in_data:
            self.send_key(_i)
            time.sleep(0.1)

        # print(f"out_data={out_data}")
        assert self.expect(out_data, timeout=timeout)
        time.sleep(0.1)

    def assert_in_out_list(
        self, inout: list[dict], timeout: float = TIMEOUT_EXPECT
    ):
        """Assert interactive in and out."""
        # print(f"inout={inout}")
        if isinstance(inout, dict):
            inout = [inout]

        for _inout in inout:
            # print(f"_inout={_inout}")
            self.assert_in_out(_inout["in"], _inout["out"], timeout=timeout)

    def close(self, terminate_flag=True, timeout_sec=TIMEOUT_CLOSE):
        """Terminates the process and closes the file descriptor."""
        ret = None

        if terminate_flag:
            print("* terminate process")
            self.process.terminate()
        try:
            ret = self.process.wait(timeout=timeout_sec)
            print(f"* ret={ret}")
        except subprocess.TimeoutExpired as _e:
            print(f"{type(_e).__name__}: {_e}")
            print("* kill process")
            self.process.kill()
            ret = self.process.wait(timeout=None)
            print(f"ret={ret}")

        os.close(self.master_fd)
        return ret


class CLITestBase:
    """CLIテスト用のヘルパークラス。"""

    DEFAULT_TIMEOUT = 10
    DEFAULT_ENCODING = "utf-8"

    def _cmdline(
        self, command: str | list[str], args: str | list[str] | None = None
    ) -> tuple[str, list]:
        """make command line list and string."""
        if isinstance(command, str):
            cmdline_list = command.split()
        else:
            cmdline_list = command

        if args:
            if isinstance(args, str):
                cmdline_list += args.split()
            else:
                cmdline_list += args

        cmdline_str = " ".join(cmdline_list)

        return (cmdline_str, cmdline_list)

    def run_command(
        self,
        command: str | list[str],
        args: str | list[str] | None = None,
        input_data: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
    ) -> subprocess.CompletedProcess:
        """コマンドを実行し、結果を返す。

        Args:
            command: 実行するコマンドのリスト。
            input_data: 標準入力に渡すデータ。
            timeout: コマンドのタイムアウト（秒）。
            cwd: コマンドを実行するディレクトリ。
            env: コマンドの環境変数。

        Returns:
            result: コマンドの実行結果。

        Raises:
            pytest.fail: コマンドの実行に失敗した場合。
            pytest.skip: コマンドが見つからない場合。
        """
        cmdline_str, cmdline_list = self._cmdline(command, args)
        print(f"\n# cmdline = {cmdline_str!r}")
        print(f"# cmdline_list = {cmdline_list}")

        try:
            if input_data:
                print(f"## input: {input_data!r}")
            result = subprocess.run(
                cmdline_list,
                capture_output=True,
                text=True,
                encoding=self.DEFAULT_ENCODING,
                input=input_data,
                timeout=timeout,
                cwd=cwd,
                env=env,
            )
            return result
        except subprocess.TimeoutExpired as _e:
            cmdline_str = " ".join(command)
            pytest.fail(f"{type(_e).__name__}: {timeout}s: {cmdline_str!r}")
        except FileNotFoundError:
            pytest.skip(f"Command not found: {command[0]}")

    def assert_out_str(
        self, label: str, out_str: str, e_out: str | list[str]
    ):
        """Assert output."""
        if not e_out:
            return

        print(f"```{label}\n{out_str}```")

        if isinstance(e_out, str):
            e_out = [e_out]

        for _o in e_out:
            print(f"## expect: {_o!r}")
            assert _o in out_str

    def assert_result(
        self,
        result: subprocess.CompletedProcess,
        e_stdout: str | list[str] = "",
        e_stderr: str | list[str] = "",
        e_ret: int | None = None,
    ):
        """Assert result"""
        self.assert_out_str("stdout", result.stdout, e_stdout)
        self.assert_out_str("stderr", result.stderr, e_stderr)
        if isinstance(e_ret, int):
            print(f"## returncode: {result.returncode} == {e_ret}")
            assert result.returncode == e_ret
        else:
            pass  # ignore
        print()

    def test_command(
        self,
        command: str | list[str],
        args: str | list[str] = "",
        input_data: Optional[str] = None,
        timeout: int = DEFAULT_TIMEOUT,
        cwd: Optional[str] = None,
        env: Optional[dict[str, str]] = None,
        e_stdout: str | list[str] = "",
        e_stderr: str | list[str] = "",
        e_ret: int | None = None,
    ) -> None:
        """Test command."""
        result = self.run_command(
            command,
            args=args,
            input_data=input_data,
            timeout=timeout,
            cwd=cwd,
            env=env,
        )
        self.assert_result(result, e_stdout, e_stderr, e_ret)

    def run_interactive_command(
        self, command: str | list[str], args: str | list[str] = ""
    ) -> "InteractiveSession":
        cmdline_str, cmdline_list = self._cmdline(command, args)
        print(f"\n# command line:  {cmdline_str!r}")

        master_fd, slave_fd = pty.openpty()
        process = subprocess.Popen(
            cmdline_list,
            stdin=slave_fd,
            stdout=slave_fd,
            stderr=slave_fd,
            close_fds=True,
            start_new_session=True,  # ** IMPORTANT **
        )
        os.close(slave_fd)
        return InteractiveSession(master_fd, process)

    def test_interactive(
        self,
        cmdline: str | list[str],
        args: str | list[str] = "",
        e_stdout: str | list[str] = "",
        e_stderr: str | list[str] = "",
        in_out: list[dict] = [],
        terminate_flag=True,
        e_ret: int | None = None,
        timeout: float = TIMEOUT_EXPECT,
    ) -> None:
        """Test interactive session."""
        session = self.run_interactive_command(cmdline, args)
        session.assert_out(e_stdout, e_stderr, timeout=timeout)  # 起動直後
        session.assert_in_out_list(in_out, timeout=timeout)  # 入出力
        ret = session.close(terminate_flag)  # 終了
        if isinstance(e_ret, int):
            assert ret == e_ret
        else:
            pass  # ignore

    def assert_output_contains(
        self,
        result: subprocess.CompletedProcess,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> None:
        """標準出力または標準エラー出力に特定の文字列が含まれていることを表明します。"""
        if stdout is not None:
            assert stdout in result.stdout, (
                f"Expected '{stdout}' in stdout, got: {result.stdout!r}"
            )
        if stderr is not None:
            assert stderr in result.stderr, (
                f"Expected '{stderr}' in stderr, got: {result.stderr!r}"
            )

    def assert_output_equals(
        self,
        result: subprocess.CompletedProcess,
        stdout: Optional[str] = None,
        stderr: Optional[str] = None,
    ) -> None:
        """stdout, stderrが特定の内容と完全に一致することを確認"""
        if stdout is not None:
            assert result.stdout == stdout, (
                f"Expected stdout: {stdout!r}, got: {result.stdout!r}"
            )
        if stderr is not None:
            assert result.stderr == stderr, (
                f"Expected stderr: {stderr!r}, got: {result.stderr!r}"
            )

    def assert_return_code(
        self, result: subprocess.CompletedProcess, expected: int
    ) -> None:
        """コマンドの終了コードが期待値と一致することを表明します。"""
        assert result.returncode == expected, (
            f"Expected return code {expected}, got {result.returncode}\n"
            f"Stdout: {result.stdout}\n"
            f"Stderr: {result.stderr}"
        )


@pytest.fixture
def cli_runner():
    """CLI テスト基盤を fixture として提供（インスタンスを返す）"""
    return CLITestBase()


# Key Constants for Interactive Testing
KEY_UP = "\x1b[A"
KEY_DOWN = "\x1b[B"
KEY_RIGHT = "\x1b[C"
KEY_LEFT = "\x1b[D"
KEY_ENTER = "\n"
KEY_EOF = "\x04"
