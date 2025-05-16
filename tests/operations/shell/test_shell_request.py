import pytest
from src.operations.shell.mock_shell_request import MockShellRequest, MockShellInteractiveRequest
from src.operations.shell.shell_result import ShellResult

def test_mock_shell_request_echo():
    req = MockShellRequest(["echo", "hello"], stdout="hello\n", returncode=0)
    result = req.execute()
    assert isinstance(result, ShellResult)
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
    assert isinstance(result, ShellResult)
    assert result.success or result.returncode == 0 