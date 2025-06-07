import pytest
from pathlib import Path
from src.domain.requests.file.file_request import FileRequest
from src.domain.requests.file.file_op_type import FileOpType
from src.domain.results.file_result import FileResult
from src.infrastructure.mock.mock_file_driver import MockFileDriver
from src.domain.constants.operation_type import OperationType

def test_file_write_and_read_with_mock():
    driver = MockFileDriver()
    path = Path("test.txt")
    
    # MockFileDriverで事前にファイルを追加
    driver._create_impl(path, "hello world")
    
    # write
    req_w = FileRequest(FileOpType.WRITE, path, content="hello world")
    result_w = req_w.execute(driver=driver)
    assert result_w.operation_type == OperationType.FILE
    assert result_w.success
    
    # read
    req_r = FileRequest(FileOpType.READ, path)
    result_r = req_r.execute(driver=driver)
    assert result_r.operation_type == OperationType.FILE
    assert result_r.success
    
    # exists
    req_e = FileRequest(FileOpType.EXISTS, path)
    result_e = req_e.execute(driver=driver)
    assert result_e.operation_type == OperationType.FILE
    assert result_e.success
    assert result_e.exists is True

def test_file_request_fail_with_mock():
    driver = MockFileDriver()
    req = FileRequest(FileOpType.READ, Path("notfound.txt"))
    result = req.execute(driver=driver)
    # モックではファイルが存在しない場合も例外は出ないが、existsはFalse
    assert result.success
    assert result.content == ""

def test_file_request_double_execute_raises():
    driver = MockFileDriver()
    path = "test_double.txt"
    req = FileRequest(FileOpType.WRITE, path, content="abc")
    req.execute(driver=driver)
    with pytest.raises(RuntimeError):
        req.execute(driver=driver)

def test_file_request_unknown_operation():
    driver = MockFileDriver()
    path = "test_unknown.txt"
    class FakeOpType:
        pass
    req = FileRequest(FakeOpType(), path)
    with pytest.raises(RuntimeError):
        req.execute(driver=driver) 