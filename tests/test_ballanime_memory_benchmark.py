from unittest.mock import patch

import psutil
import pytest

from pi0disp.utils.process_utils import (
    calculate_average_memory_usage,
    collect_memory_usage,
    format_memory_usage,
    get_ballanime_pigpiod_pids,
    get_process_pid,
)


class MockProcess:
    def __init__(self, pid, name, cmdline=None):
        self._pid = pid
        self._name = name
        self._cmdline = cmdline if cmdline is not None else [name]

    @property
    def pid(self):  # pid をプロパティに変更
        return self._pid

    def name(self):
        return self._name

    def cmdline(self):
        return self._cmdline


@pytest.fixture
def mock_psutil_processes():
    """psutil.process_iter のモックを作成するフィクスチャ"""
    mock_ballanime_process = MockProcess(
        1234, "python", ["uv", "run", "pi0disp", "ballanime", "--benchmark"]
    )
    mock_pigpiod_process = MockProcess(5678, "pigpiod")
    mock_other_process = MockProcess(9999, "other_process")
    return [mock_ballanime_process, mock_pigpiod_process, mock_other_process]


# PID 取得関数のテスト
def test_get_ballanime_pigpiod_pids_found(mock_psutil_processes):
    """ballanime と pigpiod の PID が見つかる場合のテスト"""
    with patch("psutil.process_iter", return_value=mock_psutil_processes):
        ballanime_pid, pigpiod_pid = get_ballanime_pigpiod_pids()
        assert ballanime_pid == 1234
        assert pigpiod_pid == 5678


def test_get_ballanime_pigpiod_pids_not_found():
    """ballanime や pigpiod の PID が見つからない場合のテスト"""
    with patch(
        "psutil.process_iter",
        return_value=[MockProcess(9999, "other_process")],
    ):
        ballanime_pid, pigpiod_pid = get_ballanime_pigpiod_pids()
        assert ballanime_pid is None
        assert pigpiod_pid is None


def test_get_process_pid_with_cmdline_pattern():
    """get_process_pid がコマンドラインパターンで正しく動作するかテスト"""
    mock_proc_with_cmdline = MockProcess(
        100, "python", ["/usr/bin/python", "app.py", "--env", "prod"]
    )
    with patch("psutil.process_iter", return_value=[mock_proc_with_cmdline]):
        pid = get_process_pid("python", ["app.py", "--env"])
        assert pid == 100


def test_get_process_pid_no_cmdline_pattern():
    """get_process_pid がコマンドラインパターンなしで正しく動作するかテスト"""
    mock_proc = MockProcess(200, "nginx")
    with patch("psutil.process_iter", return_value=[mock_proc]):
        pid = get_process_pid("nginx")
        assert pid == 200


def test_get_process_pid_not_found():
    """get_process_pid がプロセスを見つけられない場合にNoneを返すかテスト"""
    with patch("psutil.process_iter", return_value=[MockProcess(300, "apache")]):
        pid = get_process_pid("non_existent_process")
        assert pid is None


def test_collect_memory_usage_data():
    """メモリ使用量データを複数回収集するテスト"""
    mock_pid = 1234
    mock_memory_values = [1000, 1100, 1050, 1200]
    num_samples = len(mock_memory_values)
    interval = 0.01  # テスト用に短い間隔を設定

    with patch("psutil.Process") as MockPSProcess, patch("time.sleep"):
        mock_process_instance = MockPSProcess.return_value
        # memory_info().rss を呼び出すたびに異なる値を返すように設定
        from unittest.mock import PropertyMock

        mock_rss_mock = PropertyMock(side_effect=mock_memory_values)
        type(
            mock_process_instance.memory_info.return_value
        ).rss = mock_rss_mock  # memory_info().rss をモック

        collected_data = collect_memory_usage(
            mock_pid, num_samples=num_samples, interval=interval
        )

        assert collected_data == mock_memory_values
        MockPSProcess.assert_called_once_with(mock_pid)
        assert mock_rss_mock.call_count == num_samples


def test_collect_memory_usage_process_not_found():
    """プロセスが見つからない場合のメモリ使用量収集テスト"""
    mock_pid = 9999  # 存在しないPID
    num_samples = 3
    interval = 0.01

    with (
        patch(
            "psutil.Process", side_effect=psutil.NoSuchProcess(mock_pid)
        ) as MockPSProcess,
        patch("time.sleep"),
    ):
        collected_data = collect_memory_usage(
            mock_pid, num_samples=num_samples, interval=interval
        )
        assert collected_data == []
        MockPSProcess.assert_called_once_with(mock_pid)


def test_calculate_average_memory_usage():
    """メモリ使用量データの平均値を算出するテスト"""
    memory_data = [1000, 1100, 1050, 1200]
    expected_average = sum(memory_data) / len(memory_data)  # 1087.5

    average = calculate_average_memory_usage(memory_data)
    assert average == expected_average

    assert calculate_average_memory_usage([]) == 0.0


@pytest.mark.parametrize(
    "value, expected_string",
    [
        (100, "100 B"),
        (1023, "1023 B"),
        (1024, "1.00 KB"),
        (1024 * 1024 - 1, "1024.00 KB"),  # 1048575 バイト
        (1024 * 1024, "1.00 MB"),  # 1048576 バイト
        (1024 * 1024 * 1024 - 1, "1024.00 MB"),  # 1073741823 バイト
        (1024 * 1024 * 1024, "1.00 GB"),  # 1073741824 バイト
        (0, "0 B"),  # 修正
        (-1, "N/A"),
    ],
)
def test_format_memory_usage(value, expected_string):
    """メモリ使用量を適切な単位に自動判別してフォーマットするテスト"""
    formatted_string = format_memory_usage(value)
    assert formatted_string == expected_string


def test_ballanime_benchmark_memory_display():
    """ballanime --benchmark の出力にメモリ使用量が含まれているか確認"""
    from click.testing import CliRunner

    from pi0disp.commands.ballanime import ballanime

    runner = CliRunner()

    with (
        patch("pi0disp.commands.ballanime.ST7789V") as MockLCD,
        patch("pi0disp.commands.ballanime.draw_text") as MockDrawText,
        patch("PIL.ImageFont.truetype"),
        patch("pi0disp.commands.ballanime.BenchmarkTracker") as MockTracker,
    ):
        MockDrawText.return_value = (0, 0, 10, 10)
        mock_lcd_instance = MockLCD.return_value.__enter__.return_value
        mock_lcd_instance.size.width = 240
        mock_lcd_instance.size.height = 240

        mock_instance = MockTracker.return_value
        mock_instance.should_stop.side_effect = [False, True]
        # モックの戻り値にメモリ使用量を含める
        mock_instance.get_results.return_value = {
            "duration": 1.0,
            "avg_fps": 30.0,
            "avg_cpu": 10.0,
            "avg_pigpiod": 5.0,
            "avg_mem_ballanime": "15.00 MB",
            "avg_mem_pigpiod": "5.00 MB",
            "total_frames": 30,
        }

        result = runner.invoke(ballanime, ["--benchmark", "1", "--num-balls", "1"])

        assert result.exit_code == 0
        assert "--- Benchmark Results ---" in result.output
        assert "Avg Mem (ballanime): 15.00 MB" in result.output
        assert "Avg Mem (pigpiod): 5.00 MB" in result.output
