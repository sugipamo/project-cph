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

def test_docker_cp_with_mock():
    driver = MockFileDriver()
    src = "host.txt"
    dst = "container.txt"
    container = "mycontainer"
    # ホスト→コンテナ
    req = FileRequest(FileOpType.DOCKER_CP, src, driver=driver, dst_path=dst, container=container, to_container=True)
    with pytest.raises(FileNotFoundError):
        req.execute()

def test_docker_cp_request_attributes():
    driver = MockFileDriver()
    src = "host.txt"
    dst = "container.txt"
    container = "mycontainer"
    req = FileRequest(FileOpType.DOCKER_CP, src, driver=driver, dst_path=dst, container=container, to_container=True)
    assert req.path == src
    assert req.dst_path == dst
    assert req.container == container
    assert req.to_container is True

def test_docker_cp_localfiledriver_requires_docker_driver():
    from src.operations.file.file_driver import LocalFileDriver
    driver = LocalFileDriver()
    src = "host.txt"
    dst = "container.txt"
    container = "mycontainer"
    req = FileRequest(FileOpType.DOCKER_CP, src, driver=driver, dst_path=dst, container=container, to_container=True)
    with pytest.raises(ValueError):
        req.execute()

def test_docker_cp_file_not_found_with_mock():
    driver = MockFileDriver()
    src = "notfound.txt"
    dst = "container.txt"
    container = "mycontainer"
    req = FileRequest(FileOpType.DOCKER_CP, src, driver=driver, dst_path=dst, container=container, to_container=True)
    # ファイルがself.filesに存在しない場合、copyは何も起きないが、例外をraiseする設計ならここで確認
    with pytest.raises(Exception):
        req.execute()

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