import pytest
from src.operations.shell.shell_interactive_request import ShellInteractiveRequest
from src.operations.shell.shell_result import ShellResult

def test_shell_interactive_multiple_inputs():
    req = ShellInteractiveRequest(["python3", "-i"])
    req.start()
    req.send_input('print("foo")\n')
    req.send_input('print("bar")\n')
    lines = []
    for _ in range(6):
        line = req.read_output_line(timeout=2)
        if line:
            lines.append(line)
    assert any("foo" in l for l in lines)
    assert any("bar" in l for l in lines)
    req.send_input('import sys; print("err", file=sys.stderr)\n')
    err_lines = []
    for _ in range(5):
        err_line = req.read_error_line(timeout=2)
        if err_line:
            err_lines.append(err_line)
    assert any("err" in l for l in err_lines)
    req.send_input('exit()\n')
    result = req.wait()
    assert isinstance(result, ShellResult)
    assert result.success or result.returncode == 0
    assert "foo" in result.stdout
    assert "bar" in result.stdout 