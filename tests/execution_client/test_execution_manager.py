import pytest
import sys
from execution_client.local.client import LocalAsyncClient
from execution_client.execution_manager import ExecutionManager

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