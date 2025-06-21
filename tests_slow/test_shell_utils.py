import subprocess
import sys
import threading
from queue import Queue

import pytest

from src.infrastructure.drivers.shell.utils.shell_utils import ShellUtils


def test_run_subprocess_echo():
    result = ShellUtils.run_subprocess([sys.executable, "-c", "print('hello')"], cwd=None, env=None, inputdata=None, timeout=None)
    assert result.stdout.strip() == "hello"
    assert result.returncode == 0

def test_run_subprocess_input():
    result = ShellUtils.run_subprocess([sys.executable, "-c", "print(input())"], cwd=None, env=None, inputdata="abc\n", timeout=None)
    assert "abc" in result.stdout

def test_run_subprocess_timeout():
    with pytest.raises(subprocess.TimeoutExpired):
        ShellUtils.run_subprocess([sys.executable, "-c", "import time; time.sleep(2)"], cwd=None, env=None, inputdata=None, timeout=0.1)

def test_start_interactive_and_enqueue_output_and_drain_queue():
    proc = ShellUtils.start_interactive([sys.executable, "-c", "print('xyz')"], cwd=None, env=None)
    q = Queue()
    t = threading.Thread(target=ShellUtils.enqueue_output, args=(proc.stdout, q))
    t.start()
    t.join(timeout=2)
    lines = list(ShellUtils.drain_queue(q))
    assert any("xyz" in line for line in lines)
    proc.stdout.close()
    proc.wait()

def test_enforce_timeout():
    proc = ShellUtils.start_interactive([sys.executable, "-c", "import time; time.sleep(2)"], cwd=None, env=None)
    called = {"stopped": False}
    def stop_func(force=False):
        called["stopped"] = True
        proc.terminate()
    ShellUtils.enforce_timeout(proc, timeout=0.1, stop_func=stop_func)
    assert called["stopped"]
    proc.wait()
