import pytest
from src.domain.results.file_result import FileResult

def test_file_result_success_and_to_dict():
    r = FileResult(success=True, content="abc", path="a.txt", exists=True, op="WRITE")
    d = r.to_dict()
    assert d["success"] is True
    assert d["content"] == "abc"
    assert d["path"] == "a.txt"
    assert d["exists"] is True
    assert d["op"] == "WRITE"

def test_file_result_failure_and_exception():
    ex = ValueError("fail")
    r = FileResult(success=False, content="", path="b.txt", exists=False, op="READ", exception=ex)
    d = r.to_dict()
    assert d["success"] is False
    assert d["exception"] == "fail"
    with pytest.raises(ValueError):
        r.raise_if_error() 