import pytest
from src.execution_env.resource_handler.file_handler import LocalFileHandler
from src.command_registry.env_context import EnvContext
from src.operations.file.file_request import FileOpType, FileRequest
from src.operations.file.file_driver import MockFileDriver

class DummyConstHandler:
    pass

def make_handler():
    config = {}
    const_handler = DummyConstHandler()
    return LocalFileHandler(config, const_handler)

def test_read():
    handler = make_handler()
    driver = MockFileDriver()
    req = handler.read("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.READ
    assert req.path == "a.txt"
    req.execute(driver=driver)

def test_write():
    handler = make_handler()
    driver = MockFileDriver()
    req = handler.write("a.txt", "content")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.WRITE
    assert req.path == "a.txt"
    assert req.content == "content"
    req.execute(driver=driver)

def test_exists():
    handler = make_handler()
    driver = MockFileDriver()
    req = handler.exists("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.EXISTS
    assert req.path == "a.txt"
    req.execute(driver=driver)

def test_copy():
    handler = make_handler()
    driver = MockFileDriver()
    driver.path = driver.base_dir / "a.txt"
    driver.create("test content")
    req = handler.copy("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "a.txt"
    assert req.dst_path == "b.txt"
    req.execute(driver=driver)

def test_move():
    handler = make_handler()
    driver = MockFileDriver()
    req = handler.move("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE
    assert req.path == "a.txt"
    assert req.dst_path == "b.txt"
    req.execute(driver=driver)

def test_remove():
    handler = make_handler()
    driver = MockFileDriver()
    driver.path = driver.base_dir / "a.txt"
    driver.create("test content")
    req = handler.remove("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE
    assert req.path == "a.txt"
    req.execute(driver=driver)

def test_copytree():
    handler = make_handler()
    driver = MockFileDriver()
    req = handler.copytree("dir1", "dir2")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE
    assert req.path == "dir1"
    assert req.dst_path == "dir2"
    req.execute(driver=driver)

def test_rmtree():
    handler = make_handler()
    driver = MockFileDriver()
    driver.path = driver.base_dir / "dir1"
    driver.create("")  # ディレクトリもcreateでOK（モックなので）
    req = handler.rmtree("dir1")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE
    assert req.path == "dir1"
    req.execute(driver=driver) 