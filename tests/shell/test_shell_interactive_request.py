import pytest
from src.operations.mock.mock_shell_request import MockShellInteractiveRequest
from src.operations.result import OperationResult
from src.operations.constants.operation_type import OperationType

def test_mock_interactive_multiple_inputs():
    class DummyMockShellInteractiveRequest(MockShellInteractiveRequest):
        def _execute_core(self, driver=None):
            return None
    req = DummyMockShellInteractiveRequest(["python3", "-i"], stdout_lines=[">>> ", "foo\n", ">>> ", "bar\n", ">>> "], stderr_lines=["err\n"], returncode=0)
    req.start()
    req.send_input('print("foo")\n')
    req.send_input('print("bar")\n')
    lines = []
    for _ in range(5):
        line = req.read_output_line(timeout=2)
        if line:
            lines.append(line)
    assert any("foo" in l for l in lines)
    assert any("bar" in l for l in lines)
    req.send_input('import sys; print("err", file=sys.stderr)\n')
    err_lines = []
    for _ in range(2):
        err_line = req.read_error_line(timeout=2)
        if err_line:
            err_lines.append(err_line)
    assert any("err" in l for l in err_lines)
    req.send_input('exit()\n')
    result = req.wait()
    assert result.operation_type == OperationType.SHELL_INTERACTIVE
    assert result.success or result.returncode == 0
    assert "foo" in result.stdout or "bar" in result.stdout

def test_mock_is_running_and_wait():
    class DummyMockShellInteractiveRequest(MockShellInteractiveRequest):
        def _execute_core(self, driver=None):
            return None
    req = DummyMockShellInteractiveRequest(["sleep", "1"])
    req.start()
    assert req.is_running()
    req.wait()
    assert not req.is_running()

def test_mock_stop():
    class DummyMockShellInteractiveRequest(MockShellInteractiveRequest):
        def _execute_core(self, driver=None):
            return None
    req = DummyMockShellInteractiveRequest(["sleep", "10"])
    req.start()
    assert req.is_running()
    req.stop()
    assert not req.is_running()

def test_mock_timeout():
    class DummyMockShellInteractiveRequest(MockShellInteractiveRequest):
        def _execute_core(self, driver=None):
            return None
    req = DummyMockShellInteractiveRequest(["sleep", "10"], returncode=-9)
    req.start()
    # timeoutの模倣: stop()を呼ぶことで終了させる
    req.stop()
    assert not req.is_running()
    result = req.wait()
    assert result.returncode != 0 or result.returncode == -9 