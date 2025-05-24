import pytest
from src.operations.result.result import OperationResult

def test_operation_result_success_and_failure():
    r = OperationResult(success=True, returncode=0, stdout="ok", stderr="", content="c", exists=True, path="a.txt", op="WRITE", cmd=["echo"], start_time=1.0, end_time=2.0)
    assert r.is_success()
    assert not r.is_failure()
    assert r.elapsed_time == 1.0
    d = r.to_dict()
    assert d["success"] is True
    assert d["returncode"] == 0
    assert d["stdout"] == "ok"
    assert d["exists"] is True
    assert d["path"] == "a.txt"
    assert d["op"] == "WRITE"
    assert d["elapsed_time"] == 1.0
    j = r.to_json()
    assert "ok" in j
    s = r.summary()
    assert "OK" in s
    assert "WRITE" in s
    assert "a.txt" in s
    rep = repr(r)
    assert "OperationResult" in rep
    assert "success=True" in rep

def test_operation_result_failure_and_raise():
    r = OperationResult(success=False, returncode=1, stdout="", stderr="err", content="", exists=False, path="b.txt", op="READ", error_message="fail")
    assert not r.is_success()
    assert r.is_failure()
    s = r.summary()
    assert "FAIL" in s
    with pytest.raises(RuntimeError):
        r.raise_if_error()

def test_operation_result_exception():
    ex = ValueError("bad")
    r = OperationResult(success=False, exception=ex)
    with pytest.raises(ValueError):
        r.raise_if_error() 