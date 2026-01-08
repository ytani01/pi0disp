import logging
import os
import signal
import subprocess
import time

import psutil
import pytest

# ロガー設定
log = logging.getLogger(__name__)
if not log.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    log.addHandler(handler)
log.setLevel(logging.INFO)


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
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            preexec_fn=os.setsid,
        )
        log.info(f"Started roboface2.py with PID: {process.pid}")
        yield process
    finally:
        if process:

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

            log.info(f"Terminating process tree for PID: {process.pid}")
            kill_proc_tree(process.pid, signal.SIGTERM)
            gone, alive = psutil.wait_procs(
                [psutil.Process(process.pid)]
                if psutil.pid_exists(process.pid)
                else [],
                timeout=3,
            )
            for p in alive:
                try:
                    p.kill()
                except psutil.NoSuchProcess:
                    pass
            process.wait()


def test_cpu_memory_usage(roboface_process, duration):
    roboface_pid = roboface_process.pid
    log.info(
        f"Monitoring roboface2.py (PID: {roboface_pid}) for {duration} seconds..."
    )

    pigpiod_pid = get_pigpiod_pid()
    assert pigpiod_pid is not None, "pigpiod process not found."
    log.info(f"Monitoring pigpiod (PID: {pigpiod_pid})")

    roboface_cpu_usages = []
    roboface_mem_usages = []
    pigpiod_cpu_usages = []
    pigpiod_mem_usages = []

    sampling_interval = 1
    end_time = time.time() + duration

    roboface_proc = psutil.Process(roboface_pid)
    pigpiod_proc = psutil.Process(pigpiod_pid)

    roboface_proc.cpu_percent(interval=None)
    pigpiod_proc.cpu_percent(interval=None)
    time.sleep(sampling_interval)

    while time.time() < end_time:
        try:
            roboface_cpu = roboface_proc.cpu_percent(interval=None)
            roboface_mem = roboface_proc.memory_info().rss / (1024 * 1024)
            roboface_cpu_usages.append(roboface_cpu)
            roboface_mem_usages.append(roboface_mem)

            pigpiod_cpu = pigpiod_proc.cpu_percent(interval=None)
            pigpiod_mem = pigpiod_proc.memory_info().rss / (1024 * 1024)
            pigpiod_cpu_usages.append(pigpiod_cpu)
            pigpiod_mem_usages.append(pigpiod_mem)

            log.info(
                f"roboface CPU: {roboface_cpu:.1f}%, pigpiod CPU: {pigpiod_cpu:.1f}%"
            )
            time.sleep(sampling_interval)
        except Exception as e:
            log.error(f"Error: {e}")
            break

    if roboface_cpu_usages:
        log.info("\n--- Performance Test Results ---")
        log.info(
            f"roboface2.py: Avg CPU: {sum(roboface_cpu_usages) / len(roboface_cpu_usages):.1f}%"
        )
        log.info(
            f"pigpiod:      Avg CPU: {sum(pigpiod_cpu_usages) / len(pigpiod_cpu_usages):.1f}%"
        )

    assert roboface_process.poll() is None
