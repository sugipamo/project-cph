import pytest

from src.domain.results.shell_result import ShellResult


def test_shell_result_success_and_to_dict():
    r = ShellResult(success=True, stdout="ok", stderr="", returncode=0, cmd=["ls"])
    d = r.to_dict()
    assert d["success"] is True
    assert d["stdout"] == "ok"
    assert d["stderr"] == ""
    assert d["returncode"] == 0
    assert d["cmd"] == ["ls"]

def test_shell_result_failure_and_exception():
    ex = RuntimeError("fail")
    r = ShellResult(success=False, stdout="", stderr="err", returncode=1, cmd=["ls"], exception=ex)
    d = r.to_dict()
    assert d["success"] is False
    assert d["exception"] == "fail"
    with pytest.raises(RuntimeError):
        r.raise_if_error()
