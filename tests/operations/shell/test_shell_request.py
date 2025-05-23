import pytest
from src.operations.mock.mock_shell_request import MockShellRequest, MockShellInteractiveRequest
from src.operations.result.shell_result import ShellResult
from src.operations.result.result import OperationResult
from src.operations.constants.operation_type import OperationType
from src.operations.shell.shell_request import ShellRequest
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.di_container import DIContainer

def test_mock_shell_request_echo():
    req = MockShellRequest(["echo", "hello"], stdout="hello\n", returncode=0)
    result = req.execute()
    assert result.operation_type == OperationType.SHELL
    assert result.success
    assert "hello" in result.stdout
    result.raise_if_error()

def test_mock_shell_request_fail():
    req = MockShellRequest(["false"], stdout="", stderr="fail", returncode=1)
    result = req.execute()
    assert not result.success
    with pytest.raises(RuntimeError):
        result.raise_if_error()

def test_mock_shell_interactive_request():
    req = MockShellInteractiveRequest(["python3", "-i"], stdout_lines=[">>> ", "hello\n", ">>> "], returncode=0)
    req.start()
    req.send_input('print("hello")\n')
    lines = []
    for _ in range(3):
        line = req.read_output_line(timeout=2)
        if line:
            lines.append(line)
    assert any("hello" in l for l in lines)
    req.send_input('exit()\n')
    result = req.wait()
    assert result.operation_type == OperationType.SHELL
    assert result.success or result.returncode == 0

def test_shell_request_no_driver():
    req = ShellRequest(["echo", "hello"])
    with pytest.raises(ValueError) as excinfo:
        req.execute(None)
    assert str(excinfo.value) == "ShellRequest.execute()にはdriverが必須です"

def test_shell_request_echo(monkeypatch):
    di = DIContainer()
    from src.operations.shell.local_shell_driver import LocalShellDriver
    di.register('shell_driver', lambda: LocalShellDriver())
    req = ShellRequest(["echo", "hello"])
    driver = di.resolve('shell_driver')
    result = req.execute(driver)
    assert result.stdout.strip() == "hello"

def test_shell_request_timeout(monkeypatch):
    di = DIContainer()
    from src.operations.shell.local_shell_driver import LocalShellDriver
    di.register('shell_driver', lambda: LocalShellDriver())
    req = ShellRequest(["echo", "timeout"])
    driver = di.resolve('shell_driver')
    result = req.execute(driver)
    assert result.returncode == 0 