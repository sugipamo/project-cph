import pytest
from pathlib import Path
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.result import FileResult, OperationResult
from src.operations.file.file_driver import MockFileDriver
from src.operations.operation_type import OperationType

def test_file_write_and_read_with_mock():
    driver = MockFileDriver()
    path = Path("test.txt")
    # write
    req_w = FileRequest(FileOpType.WRITE, path, content="hello world", driver=driver)
    result_w = req_w.execute()
    assert result_w.operation_type == OperationType.FILE
    assert result_w.success
    # read
    req_r = FileRequest(FileOpType.READ, path, driver=driver)
    result_r = req_r.execute()
    assert result_r.operation_type == OperationType.FILE
    assert result_r.success
    # exists
    req_e = FileRequest(FileOpType.EXISTS, path, driver=driver)
    result_e = req_e.execute()
    assert result_e.operation_type == OperationType.FILE
    assert result_e.success
    assert result_e.exists is True

def test_file_request_fail_with_mock():
    driver = MockFileDriver()
    req = FileRequest(FileOpType.READ, Path("notfound.txt"), driver=driver)
    result = req.execute()
    # モックではファイルが存在しない場合も例外は出ないが、existsはFalse
    assert result.success
    assert result.content == ""

def test_file_request_double_execute_raises():
    driver = MockFileDriver()
    path = "test_double.txt"
    req = FileRequest(FileOpType.WRITE, path, content="abc", driver=driver)
    req.execute()
    with pytest.raises(RuntimeError):
        req.execute()

def test_file_request_unknown_operation():
    driver = MockFileDriver()
    path = "test_unknown.txt"
    class FakeOpType:
        pass
    req = FileRequest(FakeOpType(), path, driver=driver)
    with pytest.raises(RuntimeError):
        req.execute() 