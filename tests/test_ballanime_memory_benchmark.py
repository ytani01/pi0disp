import pytest
from unittest.mock import patch, MagicMock
import os
from pi0disp.utils.process_utils import get_process_pid, get_ballanime_pigpiod_pids, collect_memory_usage
import psutil

class MockProcess:
    def __init__(self, pid, name, cmdline=None):
        self._pid = pid
        self._name = name
        self._cmdline = cmdline if cmdline is not None else [name]

    @property
    def pid(self): # pid をプロパティに変更
        return self._pid

    def name(self):
        return self._name

    def cmdline(self):
        return self._cmdline

@pytest.fixture
def mock_psutil_processes():
    """psutil.process_iter のモックを作成するフィクスチャ"""
    mock_ballanime_process = MockProcess(1234, "python", ["uv", "run", "pi0disp", "ballanime", "--benchmark"])
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
    with patch("psutil.process_iter", return_value=[MockProcess(9999, "other_process")]):
        ballanime_pid, pigpiod_pid = get_ballanime_pigpiod_pids()
        assert ballanime_pid is None
        assert pigpiod_pid is None

def test_get_process_pid_with_cmdline_pattern():
    """get_process_pid がコマンドラインパターンで正しく動作するかテスト"""
    mock_proc_with_cmdline = MockProcess(100, "python", ["/usr/bin/python", "app.py", "--env", "prod"])
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
    interval = 0.01 # テスト用に短い間隔を設定

    with patch("psutil.Process") as MockPSProcess, patch("time.sleep"):
        mock_process_instance = MockPSProcess.return_value
        # memory_info().rss を呼び出すたびに異なる値を返すように設定
        from unittest.mock import PropertyMock
        mock_rss_mock = PropertyMock(side_effect=mock_memory_values)
        type(mock_process_instance.memory_info.return_value).rss = mock_rss_mock # memory_info().rss をモック

        collected_data = collect_memory_usage(mock_pid, num_samples=num_samples, interval=interval)

        assert collected_data == mock_memory_values
        MockPSProcess.assert_called_once_with(mock_pid)
        assert mock_rss_mock.call_count == num_samples

def test_collect_memory_usage_process_not_found():
    """プロセスが見つからない場合のメモリ使用量収集テスト"""
    mock_pid = 9999 # 存在しないPID
    num_samples = 3
    interval = 0.01

    with patch("psutil.Process", side_effect=psutil.NoSuchProcess(mock_pid)) as MockPSProcess, patch("time.sleep"):
        collected_data = collect_memory_usage(mock_pid, num_samples=num_samples, interval=interval)
        assert collected_data == []
        MockPSProcess.assert_called_once_with(mock_pid)