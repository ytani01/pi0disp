import psutil
import time
from typing import Optional, List

def get_process_pid(process_name: str, cmdline_pattern: Optional[List[str]] = None) -> Optional[int]:
    """
    指定されたプロセス名とコマンドラインパターンに一致するプロセスのPIDを取得する。
    pigpiod の場合は process_name="pigpiod"
    ballanime の場合は process_name="python", cmdline_pattern=["uv", "run", "pi0disp", "ballanime"]
    """
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            if proc.name() == process_name:
                if cmdline_pattern:
                    proc_cmdline = proc.cmdline()
                    # proc_cmdline が空の場合に IndexError を防ぐ
                    if proc_cmdline: 
                        matched = False
                        for i in range(len(proc_cmdline) - len(cmdline_pattern) + 1):
                            if proc_cmdline[i:i+len(cmdline_pattern)] == cmdline_pattern:
                                matched = True
                                break
                        if matched:
                            return proc.pid
                else:
                    # コマンドライン引数パターンが指定されていない場合はプロセス名のみで一致とみなす
                    return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            # プロセスが終了しているか、アクセス拒否された場合
            continue
    return None

def get_ballanime_pigpiod_pids() -> (Optional[int], Optional[int]):
    """
    ballanime と pigpiod のPIDを取得する。
    """
    ballanime_pid = get_process_pid("python", ["uv", "run", "pi0disp", "ballanime"])
    pigpiod_pid = get_process_pid("pigpiod")
    return ballanime_pid, pigpiod_pid

def collect_memory_usage(pid: int, num_samples: int = 10, interval: float = 0.1) -> List[int]:
    """
    指定されたPIDのプロセスのメモリ使用量 (RSS) を複数回収集する。
    """
    memory_data = []
    try:
        process = psutil.Process(pid)
    except (psutil.NoSuchProcess, psutil.AccessDenied):
        return [] # プロセスが見つからないかアクセス拒否された場合は空リストを返す

    try:
        for _ in range(num_samples):
            memory_data.append(process.memory_info().rss)
            time.sleep(interval)
    except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
        pass # 収集中にプロセスが終了した場合は、そこまでのデータを返す

    return memory_data