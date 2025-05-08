import pytest
from execution_client.local.client import LocalAsyncClient
import threading

def test_run_not_implemented():
    client = LocalAsyncClient()
    with pytest.raises(ValueError):
        client.run("test")
    # 正常系: commandを渡すとPopenが返る
    proc = client.run("test2", command=["echo", "hello"])
    assert proc is not None
    assert client.is_running("test2")
    client.stop("test2")

def test_run_realtime_stdout():
    client = LocalAsyncClient()
    output_lines = []
    event = threading.Event()
    def on_stdout(line):
        output_lines.append(line)
        event.set()
    # echoは即時出力される
    result = client.run("test3", command=["echo", "realtime"], realtime=True, on_stdout=on_stdout)
    proc = result.extra["popen"]
    proc.wait()
    event.wait(timeout=2)
    assert any("realtime" in l for l in output_lines)
    client.stop("test3") 