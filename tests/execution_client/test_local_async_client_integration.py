import os
import time
import tempfile
import pytest
from src.execution_client.client.local import LocalAsyncClient

@pytest.fixture
def client():
    return LocalAsyncClient()

def test_run_echo(client):
    proc = client.run(name="test_echo", command=["echo", "hello"], detach=False)
    assert proc.returncode == 0
    assert proc.stdout.strip() == "hello"

def test_build_touch_file(client):
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "testfile.txt")
        proc = client.build(name="test_build", command=["touch", file_path], cwd=tmpdir)
        assert proc.returncode == 0
        assert os.path.exists(file_path)

def test_is_running_and_stop(client):
    # sleepで長時間プロセスを起動
    proc = client.run(name="test_sleep", command=["sleep", "2"], detach=True)
    assert client.is_running("test_sleep")
    stopped = client.stop("test_sleep")
    assert stopped
    assert not client.is_running("test_sleep")

def test_remove(client):
    # removeはstopと同じ動作
    proc = client.run(name="test_remove", command=["sleep", "2"], detach=True)
    assert client.is_running("test_remove")
    removed = client.remove("test_remove")
    assert removed
    assert not client.is_running("test_remove") 