import pytest
from unittest.mock import patch, MagicMock
from src.execution_client.client.local import LocalAsyncClient
import subprocess

def test_run_command_required():
    client = LocalAsyncClient()
    with pytest.raises(ValueError):
        client.run('test', command=None)

def test_run_duplicate_name():
    client = LocalAsyncClient()
    # detach=Trueでプロセス登録
    with patch('subprocess.Popen') as mock_popen:
        mock_proc = MagicMock()
        mock_popen.return_value = mock_proc
        client.run('dup', command=['echo', 'a'], detach=True)
        # 同じnameで再度実行
        with pytest.raises(RuntimeError):
            client.run('dup', command=['echo', 'b'], detach=True)

def test_run_subprocess_run_error():
    client = LocalAsyncClient()
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(FileNotFoundError):
            client.run('test', command=['notfound'], detach=False)

def test_run_subprocess_popen_error():
    client = LocalAsyncClient()
    with patch('subprocess.Popen') as mock_popen:
        mock_popen.side_effect = OSError()
        with pytest.raises(OSError):
            client.run('test', command=['echo', 'a'], detach=True)

def test_stop_nonexistent():
    client = LocalAsyncClient()
    assert client.stop('notfound') is False

def test_stop_kill_on_timeout():
    client = LocalAsyncClient()
    mock_proc = MagicMock()
    mock_proc.terminate.side_effect = None
    mock_proc.wait.side_effect = subprocess.TimeoutExpired(cmd=['echo'], timeout=5)
    mock_proc.kill.side_effect = None
    client._processes['killme'] = mock_proc
    assert client.stop('killme') is True
    assert 'killme' not in client._processes

def test_exec_in_subprocess_run_error():
    client = LocalAsyncClient()
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = FileNotFoundError()
        with pytest.raises(FileNotFoundError):
            client.exec_in('test', ['notfound'])

def test_exec_in_subprocess_popen_error():
    client = LocalAsyncClient()
    with patch('subprocess.Popen') as mock_popen:
        mock_popen.side_effect = OSError()
        with pytest.raises(OSError):
            client.exec_in('test', ['echo', 'a'], realtime=True)

def test_is_running_nonexistent():
    client = LocalAsyncClient()
    assert client.is_running('notfound') is False 