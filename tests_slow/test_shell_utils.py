import pytest
import subprocess
import sys
import os
import threading
from queue import Queue
from src.infrastructure.drivers.shell.utils.shell_utils import ShellUtils

def test_run_subprocess_echo():
    result = ShellUtils.run_subprocess([sys.executable, "-c", "print('hello')"])
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0

def test_run_subprocess_input():
    result = ShellUtils.run_subprocess([sys.executable, "-c", "print(input())"], inputdata="abc\n")
    assert "abc" in result.stdout

def test_run_subprocess_timeout():
    with pytest.raises(subprocess.TimeoutExpired):
        ShellUtils.run_subprocess([sys.executable, "-c", "import time; time.sleep(2)"] , timeout=0.1)

def test_start_interactive_and_enqueue_output_and_drain_queue():
    proc = ShellUtils.start_interactive([sys.executable, "-c", "print('xyz')"])
    q = Queue()
    t = threading.Thread(target=ShellUtils.enqueue_output, args=(proc.stdout, q))
    t.start()
    t.join(timeout=2)
    lines = list(ShellUtils.drain_queue(q))
    assert any("xyz" in l for l in lines)
    proc.stdout.close()
    proc.wait()

def test_enforce_timeout():
    proc = ShellUtils.start_interactive([sys.executable, "-c", "import time; time.sleep(2)"])
    called = {"stopped": False}
    def stop_func(force=False):
        called["stopped"] = True
        proc.terminate()
    ShellUtils.enforce_timeout(proc, timeout=0.1, stop_func=stop_func)
    assert called["stopped"]
    proc.wait() 