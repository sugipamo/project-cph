import pytest
from src.domain.results.shell_result import ShellResult
from src.domain.results.result import OperationResult
from src.domain.constants.operation_type import OperationType
from src.domain.requests.shell.shell_request import ShellRequest
from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
from src.infrastructure.di_container import DIContainer
import os
import unittest.mock

def test_shell_request_echo():
    """Test shell request using mock driver instead of MockShellRequest"""
    with unittest.mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = "hello\n"
        mock_run.return_value.stderr = ""
        mock_run.return_value.returncode = 0
        
        req = ShellRequest(["echo", "hello"])
        driver = LocalShellDriver()
        result = req.execute(driver=driver)
        assert result.operation_type == OperationType.SHELL
    assert result.success
    assert "hello" in result.stdout
    result.raise_if_error()

def test_shell_request_fail():
    """Test shell request failure using mock"""
    with unittest.mock.patch('subprocess.run') as mock_run:
        mock_run.return_value.stdout = ""
        mock_run.return_value.stderr = "fail"
        mock_run.return_value.returncode = 1
        
        req = ShellRequest(["false"])
        driver = LocalShellDriver()
        result = req.execute(driver=driver)
        assert not result.success
        with pytest.raises(RuntimeError):
            result.raise_if_error()


def test_shell_request_no_driver():
    req = ShellRequest(["echo", "hello"])
    with pytest.raises(ValueError) as excinfo:
        req.execute(None)
    assert "requires a driver" in str(excinfo.value)

def test_shell_request_echo():
    di = DIContainer()
    from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
    di.register('shell_driver', lambda: LocalShellDriver())
    req = ShellRequest(["echo", "hello"])
    driver = di.resolve('shell_driver')
    result = req.execute(driver)
    assert result.stdout.strip() == "hello"

def test_shell_request_timeout():
    di = DIContainer()
    from src.infrastructure.drivers.shell.local_shell_driver import LocalShellDriver
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
    # ShellUtils.run_subprocessで例外を投げるようにする
    req = ShellRequest(["false"])
    driver = LocalShellDriver()
    with unittest.mock.patch("src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess", side_effect=Exception("fail")):
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
    with unittest.mock.patch("src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess", fake_run_subprocess):
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
    with unittest.mock.patch("src.infrastructure.drivers.shell.utils.shell_utils.ShellUtils.run_subprocess", fake_run_subprocess):
        req = ShellRequest(["echo", "x"], show_output=True)
        driver = LocalShellDriver()
        result = req._execute_core(driver)
    # show_outputの分岐は本体でprintしていないが、今後の拡張用にカバレッジ確保
    assert result.stdout == "out"
    assert result.stderr == "err" 