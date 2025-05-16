import pytest
import time
from src.execution_client.client.local import LocalAsyncClient
from src.shell_process import ShellProcessOptions

@pytest.fixture
def client():
    return LocalAsyncClient()

def test_run_and_list(client):
    name = "testproc"
    proc = client.run(name=name, command=["echo", "hello"], detach=False, realtime=False)
    assert proc.returncode == 0
    assert proc.stdout.strip() == "hello"
    # detach=Falseなのでプロセス管理には載らない
    assert name not in client.list()

def test_run_detach_and_stop(client):
    name = "testproc2"
    proc = client.run(name=name, command=["sleep", "10"], detach=True, realtime=False)
    assert name in client.list()
    assert client.is_running(name)
    stopped = client.stop(name)
    assert stopped
    assert name not in client.list()
    assert not client.is_running(name)

def test_remove(client):
    name = "testproc3"
    proc = client.run(name=name, command=["sleep", "2"], detach=True, realtime=False)
    assert name in client.list()
    removed = client.remove(name)
    assert removed
    assert name not in client.list()

def test_run_many(client):
    cmds = [ShellProcessOptions(cmd=["echo", "A"]), ShellProcessOptions(cmd=["echo", "B"])]
    results = client.run_many(cmds)
    outs = [r.stdout.strip() for r in results]
    assert "A" in outs and "B" in outs 