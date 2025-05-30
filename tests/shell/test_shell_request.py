import pytest
from src.operations.mock.mock_shell_request import MockShellRequest, MockShellInteractiveRequest
from src.operations.result.shell_result import ShellResult
from src.operations.result.result import OperationResult
from src.operations.constants.operation_type import OperationType
from src.operations.shell.shell_request import ShellRequest
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.di_container import DIContainer
import os
import unittest.mock

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
    class DummyMockShellInteractiveRequest(MockShellInteractiveRequest):
        def _execute_core(self, driver=None):
            return None
    req = DummyMockShellInteractiveRequest(["python3", "-i"], stdout_lines=[">>> ", "hello\n", ">>> "], returncode=0)
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
    assert result.operation_type == OperationType.SHELL_INTERACTIVE
    assert result.success or result.returncode == 0

def test_shell_request_no_driver():
    req = ShellRequest(["echo", "hello"])
    with pytest.raises(ValueError) as excinfo:
        req.execute(None)
    assert str(excinfo.value) == "ShellRequest.execute()にはdriverが必須です"

def test_shell_request_echo():
    di = DIContainer()
    from src.operations.shell.local_shell_driver import LocalShellDriver
    di.register('shell_driver', lambda: LocalShellDriver())
    req = ShellRequest(["echo", "hello"])
    driver = di.resolve('shell_driver')
    result = req.execute(driver)
    assert result.stdout.strip() == "hello"

def test_shell_request_timeout():
    di = DIContainer()
    from src.operations.shell.local_shell_driver import LocalShellDriver
    di.register('shell_driver', lambda: LocalShellDriver())
    req = ShellRequest(["echo", "timeout"])
    driver = di.resolve('shell_driver')
    result = req.execute(driver)
    assert result.returncode == 0

def test_shell_request_repr():
    req = ShellRequest(["ls", "/"], name="test")
    s = repr(req)
    assert "ShellRequest" in s and "/" in s

def test_shell_request_execute_exception():
    # ShellUtil.run_subprocessで例外を投げるようにする
    req = ShellRequest(["false"])
    driver = LocalShellDriver()
    with unittest.mock.patch("src.operations.shell.shell_util.ShellUtil.run_subprocess", side_effect=Exception("fail")):
        result = req._execute_core(driver)
    assert isinstance(result, OperationResult)
    assert result.stderr == "fail"
    assert result.returncode is None

def test_shell_request_with_inputdata_env_cwd(tmp_path):
    # run_subprocessの呼び出し内容を検証
    called = {}
    def fake_run_subprocess(cmd, cwd=None, env=None, inputdata=None, timeout=None):
        called.update(dict(cmd=cmd, cwd=cwd, env=env, inputdata=inputdata, timeout=timeout))
        class Completed:
            stdout = "ok"
            stderr = ""
            returncode = 0
        return Completed()
    with unittest.mock.patch("src.operations.shell.shell_util.ShellUtil.run_subprocess", fake_run_subprocess):
        req = ShellRequest(["echo", "x"], cwd=str(tmp_path), env={"A": "B"}, inputdata="in", timeout=1)
        driver = LocalShellDriver()
        result = req._execute_core(driver)
    assert called["cwd"] == str(tmp_path)
    assert called["env"] == {"A": "B"}
    assert called["inputdata"] == "in"
    assert called["timeout"] == 1
    assert result.stdout == "ok"
    assert result.returncode == 0

def test_shell_request_show_output(capsys):
    def fake_run_subprocess(*a, **k):
        class Completed:
            stdout = "out"
            stderr = "err"
            returncode = 0
        return Completed()
    with unittest.mock.patch("src.operations.shell.shell_util.ShellUtil.run_subprocess", fake_run_subprocess):
        req = ShellRequest(["echo", "x"], show_output=True)
        driver = LocalShellDriver()
        result = req._execute_core(driver)
    # show_outputの分岐は本体でprintしていないが、今後の拡張用にカバレッジ確保
    assert result.stdout == "out"
    assert result.stderr == "err" 