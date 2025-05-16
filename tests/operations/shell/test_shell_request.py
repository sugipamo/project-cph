import pytest
from src.operations.shell.shell_request import ShellRequest
from src.operations.shell.shell_result import ShellResult
from src.operations.shell.shell_interactive_request import ShellInteractiveRequest


def test_shell_request_echo():
    req = ShellRequest(["echo", "hello"])
    result = req.execute()
    assert isinstance(result, ShellResult)
    assert result.success
    assert "hello" in result.stdout
    result.raise_if_error()

def test_shell_request_fail():
    req = ShellRequest(["false"])
    result = req.execute()
    assert not result.success
    with pytest.raises(RuntimeError):
        result.raise_if_error()

def test_shell_interactive_request():
    req = ShellInteractiveRequest(["python3", "-i"])
    req.start()
    req.send_input('print("hello")\n')
    # Pythonのプロンプトや出力を複数行読む必要がある
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