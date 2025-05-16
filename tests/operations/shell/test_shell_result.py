import pytest
from src.operations.shell.shell_result import ShellResult
from src.operations.shell.shell_request import ShellRequest

def test_shell_result_methods():
    req = ShellRequest(["echo", "abc"])
    result = ShellResult(stdout="abc\n", stderr="", returncode=0, request=req)
    d = result.to_dict()
    assert d["stdout"] == "abc\n"
    assert d["returncode"] == 0
    assert "abc" in result.summary()
    assert isinstance(result.to_json(), str)
    assert result.is_success()
    assert not result.is_failure()

    # 異常系
    result_fail = ShellResult(stdout="", stderr="fail", returncode=1, request=req, error_message="fail")
    assert not result_fail.is_success()
    assert result_fail.is_failure()
    with pytest.raises(RuntimeError):
        result_fail.raise_if_error() 