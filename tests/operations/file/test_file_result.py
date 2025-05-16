import pytest
from src.operations.result import OperationResult
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.operation_type import OperationType
from src.operations.file.file_driver import MockFileDriver

def test_file_result_methods():
    driver = MockFileDriver()
    req = FileRequest(FileOpType.READ, "foo.txt", driver=driver)
    result = OperationResult(success=True, content="abc", exists=True, path="foo.txt", op=FileOpType.READ, request=req)
    d = result.to_dict()
    assert d["success"] is True
    assert d["content"] == "abc"
    assert d["op"] == str(FileOpType.READ)
    assert "foo.txt" in result.summary()
    assert isinstance(result.to_json(), str)
    assert result.is_success()
    assert not result.is_failure()

    # 異常系
    result_fail = OperationResult(success=False, content=None, exists=False, path="bar.txt", op=FileOpType.READ, request=req, error_message="fail")
    assert not result_fail.is_success()
    assert result_fail.is_failure()
    with pytest.raises(RuntimeError):
        result_fail.raise_if_error() 