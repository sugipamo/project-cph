import pytest
from src.execution_env.resource_handler.file_handler import LocalFileHandler
from src.operations.file.file_request import FileOpType, FileRequest

class DummyConstHandler:
    pass

def make_handler():
    config = {}
    const_handler = DummyConstHandler()
    return LocalFileHandler(config, const_handler)

def test_read():
    handler = make_handler()
    req = handler.read("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.READ
    assert req.path == "a.txt"

def test_write():
    handler = make_handler()
    req = handler.write("a.txt", "content")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.WRITE
    assert req.path == "a.txt"
    assert req.content == "content"

def test_exists():
    handler = make_handler()
    req = handler.exists("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.EXISTS
    assert req.path == "a.txt"

def test_copy():
    handler = make_handler()
    req = handler.copy("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "a.txt"
    assert req.dst_path == "b.txt"

def test_move():
    handler = make_handler()
    req = handler.move("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE
    assert req.path == "a.txt"
    assert req.dst_path == "b.txt"

def test_remove():
    handler = make_handler()
    req = handler.remove("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE
    assert req.path == "a.txt"

def test_copytree():
    handler = make_handler()
    req = handler.copytree("dir1", "dir2")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE
    assert req.path == "dir1"
    assert req.dst_path == "dir2"

def test_rmtree():
    handler = make_handler()
    req = handler.rmtree("dir1")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE
    assert req.path == "dir1" 