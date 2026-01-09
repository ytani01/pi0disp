import pytest
from unittest.mock import patch, MagicMock
import os
from pi0disp.utils.process_utils import get_process_pid, get_ballanime_pigpiod_pids

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