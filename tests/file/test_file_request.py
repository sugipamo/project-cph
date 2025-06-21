from pathlib import Path

import pytest

from src.infrastructure.mock.mock_file_driver import MockFileDriver
from src.operations.constants.operation_type import OperationType
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest
from src.operations.results.file_result import FileResult


def test_file_write_and_read_with_mock():
    driver = MockFileDriver(base_dir=Path("."))
    path = Path("test.txt")

    # MockFileDriverで事前にファイルを追加
    driver._create_impl(path, "hello world")

    # write
    req_w = FileRequest(FileOpType.WRITE, path, content="hello world", dst_path=None, debug_tag=None, name=None)
    logger = None
    result_w = req_w.execute_operation(driver=driver, logger=logger)
    assert result_w.operation_type == OperationType.FILE
    assert result_w.success

    # read
    req_r = FileRequest(FileOpType.READ, path, content=None, dst_path=None, debug_tag=None, name=None)
    result_r = req_r.execute_operation(driver=driver, logger=logger)
    assert result_r.operation_type == OperationType.FILE
    assert result_r.success

    # exists
    req_e = FileRequest(FileOpType.EXISTS, path, content=None, dst_path=None, debug_tag=None, name=None)
    result_e = req_e.execute_operation(driver=driver, logger=logger)
    assert result_e.operation_type == OperationType.FILE
    assert result_e.success
    assert result_e.exists is True

def test_file_request_fail_with_mock():
    driver = MockFileDriver(base_dir=Path("."))
    req = FileRequest(FileOpType.READ, Path("notfound.txt"), content=None, dst_path=None, debug_tag=None, name=None)
    logger = None
    result = req.execute_operation(driver=driver, logger=logger)
    # モックではファイルが存在しない場合も例外は出ないが、existsはFalse
    assert result.success
    assert result.content == ""


