import pytest
from unittest.mock import MagicMock, patch
from src.execution_client.execution_manager import ExecutionManager
from src.execution_client.types import ExecutionResult

def make_result(returncode=0, stdout='', stderr='', extra=None):
    r = MagicMock()
    r.returncode = returncode
    r.stdout = stdout
    r.stderr = stderr
    r.extra = extra or {}
    return r

def test_run_and_measure_is_container_running():
    client = MagicMock()
    client.is_container_running.return_value = True
    exec_result = MagicMock(returncode=0, stdout='ok', stderr='')
    client.exec_in.return_value = exec_result
    manager = ExecutionManager(client)
    result = manager.run_and_measure('c', ['echo'])
    assert isinstance(result, ExecutionResult)
    assert result.returncode == 0
    assert result.stdout == 'ok'
    assert result.extra['timeout'] is False
    client.exec_in.assert_called_once()
    client.remove.assert_not_called()

def test_run_and_measure_input_data():
    client = MagicMock()
    client.is_container_running.return_value = False
    client.run.return_value = make_result(returncode=0, stdout='out', stderr='err')
    manager = ExecutionManager(client)
    result = manager.run_and_measure('c', ['echo'], input='foo')
    assert result.returncode == 0
    assert result.stdout == 'out'
    assert result.stderr == 'err'
    assert result.extra['timeout'] is False
    client.run.assert_called_once()
    client.remove.assert_not_called()

def test_run_and_measure_detach_true_with_popen():
    client = MagicMock()
    client.is_container_running.return_value = False
    proc = MagicMock()
    proc.communicate.return_value = ('out', 'err')
    proc.returncode = 0
    client.run.return_value = make_result(extra={'popen': proc})
    manager = ExecutionManager(client)
    with patch('time.perf_counter', side_effect=[0, 0.1]):
        result = manager.run_and_measure('c', ['echo'], timeout=1)
    assert result.returncode == 0
    assert result.stdout == 'out'
    assert result.stderr == 'err'
    assert result.extra['timeout'] is False
    client.remove.assert_called_once_with('c')

def test_run_and_measure_detach_true_with_popen_timeout():
    client = MagicMock()
    client.is_container_running.return_value = False
    proc = MagicMock()
    proc.communicate.side_effect = [Exception(), ('out', 'err')]
    proc.returncode = 1
    client.run.return_value = make_result(extra={'popen': proc})
    manager = ExecutionManager(client)
    with patch('time.perf_counter', side_effect=[0, 0.2]):
        result = manager.run_and_measure('c', ['echo'], timeout=0.1)
    assert result.returncode == 1
    assert result.extra['timeout'] is True
    client.remove.assert_called_once_with('c')

def test_run_and_measure_detach_true_no_popen():
    client = MagicMock()
    client.is_container_running.return_value = False
    client.run.return_value = make_result(extra={'popen': None})
    client.is_running.side_effect = [True, False]
    manager = ExecutionManager(client)
    with patch('time.perf_counter', side_effect=[0, 0.06]):
        with patch('time.sleep') as mock_sleep:
            result = manager.run_and_measure('c', ['echo'], timeout=0.05)
    assert result.returncode is None
    assert result.extra['timeout'] is False or result.extra['timeout'] is True
    client.remove.assert_called_once_with('c') 