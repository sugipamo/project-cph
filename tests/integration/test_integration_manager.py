import pytest
import sys
import threading
import shutil
from src.execution_client.client.local import LocalAsyncClient
from src.execution_client.client.container import ContainerClient
from src.execution_client.execution_manager import ExecutionManager

def test_integration_local_manager():
    client = LocalAsyncClient()
    manager = ExecutionManager(client)
    # run_and_measureでsleep
    result = manager.run_and_measure("integration1", ["sleep", "0.1"])
    # 精度誤差を考慮して閾値を0.09に緩和
    assert result.extra["elapsed"] >= 0.09
    # realtime出力取得
    output_lines = []
    event = threading.Event()
    def on_stdout(line):
        output_lines.append(line)
        event.set()
    result2 = client.run("integration2", command=["echo", "integration"], realtime=True, on_stdout=on_stdout)
    proc = result2.extra["popen"]
    proc.wait()
    event.wait(timeout=2)
    assert any("integration" in l for l in output_lines)
    client.stop("integration2")