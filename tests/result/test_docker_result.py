import pytest

from src.operations.results.docker_result import DockerResult


def test_docker_result_success_and_to_dict():
    r = DockerResult(success=True, stdout="ok", stderr="", returncode=0, op="RUN")
    d = r.to_dict()
    assert d["success"] is True
    assert d["stdout"] == "ok"
    assert d["stderr"] == ""
    assert d["returncode"] == 0
    assert d["op"] == "RUN"

def test_docker_result_failure_and_exception():
    ex = RuntimeError("fail")
    r = DockerResult(success=False, stdout="", stderr="err", returncode=1, op="STOP", exception=ex)
    d = r.to_dict()
    assert d["success"] is False
    assert d["exception"] == "fail"
    with pytest.raises(RuntimeError):
        r.raise_if_error()
