import pytest
from pathlib import Path
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.file.file_result import FileResult
from src.operations.file.file_driver import MockFileDriver

def test_file_write_and_read_with_mock():
    driver = MockFileDriver()
    path = Path("test.txt")
    # write
    req_w = FileRequest(FileOpType.WRITE, path, content="hello world", driver=driver)
    result_w = req_w.execute()
    assert isinstance(result_w, FileResult)
    assert result_w.success
    # read
    req_r = FileRequest(FileOpType.READ, path, driver=driver)
    result_r = req_r.execute()
    assert isinstance(result_r, FileResult)
    assert result_r.success
    # exists
    req_e = FileRequest(FileOpType.EXISTS, path, driver=driver)
    result_e = req_e.execute()
    assert isinstance(result_e, FileResult)
    assert result_e.success
    assert result_e.exists is True

def test_file_request_fail_with_mock():
    driver = MockFileDriver()
    req = FileRequest(FileOpType.READ, Path("notfound.txt"), driver=driver)
    result = req.execute()
    # モックではファイルが存在しない場合も例外は出ないが、existsはFalse
    assert result.success
    assert result.content == "" 