import logging
import os
import signal
import subprocess
import time

import psutil
import pytest

# ロガー設定をファイルのトップレベルで一度だけ実行
log = logging.getLogger(__name__)
if not log.handlers:  # 既にハンドラが設定されていなければ設定する
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
log.setLevel(logging.INFO)  # デバッグログも表示したい場合は DEBUG に変更


# pigpiodプロセスのPIDを検索
def get_pigpiod_pid():
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if "pigpiod" in proc.name():
                return proc.pid
            if proc.cmdline() and "pigpiod" in " ".join(proc.cmdline()):
                return proc.pid
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ):
            pass
    return None


@pytest.fixture(scope="module")
def roboface_process():
    # 今回は roboface2.py をベースラインとして起動
    cmd = ["uv", "run", "samples/roboface2.py", "--random"]
    process = None
    try:
        # Popenでサブプロセスとして起動
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,  # プロセスグループを作成
        )
        log.info(f"Started roboface2.py with PID: {process.pid}")
        yield process
    finally:
        if process:
            # プロセスツリー全体を停止させるための関数
            def kill_proc_tree(pid, sig=signal.SIGTERM, include_parent=True):
                try:
                    parent = psutil.Process(pid)
                    children = parent.children(recursive=True)
                    for child in children:
                        child.send_signal(sig)
                    if include_parent:
                        parent.send_signal(sig)
                except psutil.NoSuchProcess:
                    pass

            # 1. まず SIGTERM で優しく終了を試みる
            log.info(f"Terminating process tree for PID: {process.pid}")
            kill_proc_tree(process.pid, signal.SIGTERM)

            # 2. しばらく待機
            gone, alive = psutil.wait_procs(
                [psutil.Process(process.pid)]
                if psutil.pid_exists(process.pid)
                else [],
                timeout=3,
            )

            # 3. まだ生きていれば SIGKILL で強制終了
            for p in alive:
                log.warning(f"Process {p.pid} did not terminate, killing it.")
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass

            # 4. OSによるプロセスリソースの完全な回収 (Reaping)
            process.wait()

            stdout, stderr = process.communicate()
            if stdout:
                log.info(f"roboface2.py stdout captured (len: {len(stdout)})")
            if stderr:
                log.error(f"roboface2.py stderr:\n{stderr.decode()}")


def test_cpu_memory_usage(roboface_process, duration):
    roboface_pid = roboface_process.pid
    log.info(
        f"Monitoring roboface2.py (PID: {roboface_pid}) for {duration} seconds..."
    )

    # pigpiodのPIDを取得
    pigpiod_pid = get_pigpiod_pid()
    assert pigpiod_pid is not None, "pigpiod process not found."
    log.info(f"Monitoring pigpiod (PID: {pigpiod_pid})")

    roboface_cpu_usages = []
    roboface_mem_usages = []  # MB単位
    pigpiod_cpu_usages = []
    pigpiod_mem_usages = []  # MB単位

    sampling_interval = 1  # 1秒ごとにサンプリング
    end_time = time.time() + duration

    roboface_proc = psutil.Process(roboface_pid)
    pigpiod_proc = psutil.Process(pigpiod_pid)

    # 最初の瞬間的なCPU使用率の計測を避けるために一度呼び出す
    roboface_proc.cpu_percent(interval=None)
    pigpiod_proc.cpu_percent(interval=None)
    time.sleep(sampling_interval)  # 最初のサンプリングをずらす

    while time.time() < end_time:
        try:
            # roboface2.py プロセスの情報
            roboface_cpu = roboface_proc.cpu_percent(interval=None)
            roboface_mem = roboface_proc.memory_info().rss / (
                1024 * 1024
            )  # bytes to MB
            roboface_cpu_usages.append(roboface_cpu)
            roboface_mem_usages.append(roboface_mem)

            # pigpiod プロセスの情報
            pigpiod_cpu = pigpiod_proc.cpu_percent(interval=None)
            pigpiod_mem = pigpiod_proc.memory_info().rss / (
                1024 * 1024
            )  # bytes to MB
            pigpiod_cpu_usages.append(pigpiod_cpu)
            pigpiod_mem_usages.append(pigpiod_mem)

            log.info(
                f"Time left: {round(end_time - time.time())}s "
                f"roboface CPU: {roboface_cpu:.2f}%, MEM: {roboface_mem:.2f}MB | "
                f"pigpiod CPU: {pigpiod_cpu:.2f}%, MEM: {pigpiod_mem:.2f}MB"
            )
            time.sleep(sampling_interval)
        except (
            psutil.NoSuchProcess,
            psutil.AccessDenied,
            psutil.ZombieProcess,
        ) as e:
            log.warning(f"Process disappeared during monitoring: {e}")
            break
        except Exception as e:
            log.error(f"Error during monitoring: {e}")
            break

    # 結果の集計と出力
    if roboface_cpu_usages and pigpiod_cpu_usages:
        avg_roboface_cpu = sum(roboface_cpu_usages) / len(roboface_cpu_usages)
        max_roboface_cpu = max(roboface_cpu_usages)
        avg_roboface_mem = sum(roboface_mem_usages) / len(roboface_mem_usages)
        max_roboface_mem = max(roboface_mem_usages)

        avg_pigpiod_cpu = sum(pigpiod_cpu_usages) / len(pigpiod_cpu_usages)
        max_pigpiod_cpu = max(pigpiod_cpu_usages)
        avg_pigpiod_mem = sum(pigpiod_mem_usages) / len(pigpiod_mem_usages)
        max_pigpiod_mem = max(pigpiod_mem_usages)

        log.info("\n--- Performance Test Results ---")
        log.info(f"roboface2.py (PID: {roboface_pid}):")
        log.info(f"  Average CPU: {avg_roboface_cpu:.2f}%")
        log.info(f"  Max CPU: {max_roboface_cpu:.2f}%")
        log.info(f"  Average Memory (RSS): {avg_roboface_mem:.2f}MB")
        log.info(f"  Max Memory (RSS): {max_roboface_mem:.2f}MB")
        log.info(f"pigpiod (PID: {pigpiod_pid}):")
        log.info(f"  Average CPU: {avg_pigpiod_cpu:.2f}%")
        log.info(f"  Max CPU: {max_pigpiod_cpu:.2f}%")
        log.info(f"  Average Memory (RSS): {avg_pigpiod_mem:.2f}MB")
        log.info(f"  Max Memory (RSS): {max_pigpiod_mem:.2f}MB")
        log.info("------------------------------")
    else:
        log.warning("No performance data collected.")

    # 少なくとも、プロセスが途中で終了しなかったことを確認するアサート
    assert roboface_process.poll() is None, (
        "roboface2.py process terminated unexpectedly."
    )
