import logging
import os
import signal
import subprocess
import time
import psutil
import pytest

log = logging.getLogger(__name__)
if not log.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    log.addHandler(handler)
log.setLevel(logging.INFO)

def get_pigpiod_pid():
    for proc in psutil.process_iter(["pid", "name", "cmdline"]):
        try:
            if "pigpiod" in proc.name() or (proc.cmdline() and "pigpiod" in " ".join(proc.cmdline())):
                return proc.pid
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            pass
    return None

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

@pytest.fixture
def ballanime_process(request):
    mode = getattr(request, "param", "simple")
    cmd = ["uv", "run", "pi0disp", "ballanime", "--mode", mode, "--num-balls", "10", "--fps", "30"]
    process = subprocess.Popen(cmd, preexec_fn=os.setsid)
    log.info(f"Started ballanime --mode {mode} (PID: {process.pid})")
    yield process, mode
    kill_proc_tree(process.pid)
    process.wait()

@pytest.mark.parametrize("ballanime_process", ["simple", "fast"], indirect=True)
def test_ballanime_performance_comparison(ballanime_process, duration):
    proc_obj, mode = ballanime_process
    pid = proc_obj.pid
    
    pigpiod_pid = get_pigpiod_pid()
    assert pigpiod_pid is not None
    
    proc = psutil.Process(pid)
    pigpiod_proc = psutil.Process(pigpiod_pid)
    
    cpu_usages = []
    pigpiod_cpu_usages = []
    
    # Warm up
    proc.cpu_percent(interval=None)
    pigpiod_proc.cpu_percent(interval=None)
    time.sleep(1)
    
    end_time = time.time() + duration
    while time.time() < end_time:
        cpu_usages.append(proc.cpu_percent(interval=None))
        pigpiod_cpu_usages.append(pigpiod_proc.cpu_percent(interval=None))
        time.sleep(1)
    
    avg_cpu = sum(cpu_usages) / len(cpu_usages) if cpu_usages else 0
    avg_pigpiod_cpu = sum(pigpiod_cpu_usages) / len(pigpiod_cpu_usages) if pigpiod_cpu_usages else 0
    
    log.info(f"\nResults for mode: {mode}")
    log.info(f"  App Average CPU: {avg_cpu:.2f}%")
    log.info(f"  pigpiod Average CPU: {avg_pigpiod_cpu:.2f}%")
    log.info(f"  Total CPU Impact: {avg_cpu + avg_pigpiod_cpu:.2f}%")
