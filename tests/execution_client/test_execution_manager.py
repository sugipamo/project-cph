import pytest
import sys
from src.execution_client.local import LocalAsyncClient
from execution_client.execution_manager import ExecutionManager, AbstractExecutionManager

@pytest.mark.parametrize("sleep_sec", [0.5, 1.0])
def test_run_and_measure_sleep(sleep_sec):
    client = LocalAsyncClient()
    manager = ExecutionManager(client)
    # cross-platform sleep command
    if sys.platform.startswith("win"):
        command = ["timeout", "/T", str(int(sleep_sec))]
    else:
        command = ["sleep", str(sleep_sec)]
    result = manager.run_and_measure("test_sleep", command)
    assert result.returncode == 0
    assert result.extra["elapsed"] >= sleep_sec
    assert result.extra["elapsed"] < sleep_sec + 0.5  # 許容誤差
    assert not result.extra.get("timeout", False)

def test_run_and_measure_timeout():
    client = LocalAsyncClient()
    manager = ExecutionManager(client)
    if sys.platform.startswith("win"):
        command = ["timeout", "/T", "2"]
    else:
        command = ["sleep", "2"]
    result = manager.run_and_measure("test_timeout", command, timeout=1)
    assert result.extra["timeout"] is True
    assert result.extra["elapsed"] < 1.5

class DummyManager(AbstractExecutionManager):
    def run_and_measure(self, name, command, timeout=None, **kwargs):
        return "dummy"

def test_abstract_execution_manager():
    manager = DummyManager()
    assert manager.run_and_measure("n", ["echo"]) == "dummy" 