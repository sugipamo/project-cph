import pytest
from src.execution_env.resource_handler.file_handler import DockerFileHandler
from src.operations.file.file_request import FileOpType, FileRequest
from src.operations.docker.docker_file_request import DockerFileRequest
from src.operations.docker.docker_driver import MockDockerDriver

class MockConstHandler:
    def __init__(self, workspace_path="/workspace", container_name="test_container"):
        self.workspace_path = workspace_path
        self._container_name = container_name
    @property
    def container_name(self):
        return self._container_name

def make_handler():
    config = {}
    const_handler = MockConstHandler()
    return DockerFileHandler(config, const_handler)

def test_copy_in_container():
    handler = make_handler()
    req = handler.copy("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "a.txt"
    assert req.dst_path == "b.txt"

def test_copy_host_to_container():
    handler = make_handler()
    handler.const_handler.workspace_path = "/workspace"
    req = handler.copy("/host/file.txt", "in_container.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == "/host/file.txt"
    assert req.dst_path == "in_container.txt"
    assert req.container == "test_container"
    assert req.to_container is True

def test_copy_container_to_host():
    handler = make_handler()
    handler.const_handler.workspace_path = "/workspace"
    req = handler.copy("in_container.txt", "/host/file.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == "in_container.txt"
    assert req.dst_path == "/host/file.txt"
    assert req.container == "test_container"
    assert req.to_container is False

def test_move_in_container():
    handler = make_handler()
    req = handler.move("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE
    assert req.path == "a.txt"
    assert req.dst_path == "b.txt"

def test_move_host_to_container_and_reverse():
    handler = make_handler()
    handler.const_handler.workspace_path = "/workspace"
    req = handler.move("/host/file.txt", "in_container.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == "/host/file.txt"
    assert req.dst_path == "in_container.txt"
    assert req.container == "test_container"
    assert req.to_container is True

def test_remove_in_container():
    handler = make_handler()
    req = handler.remove("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE
    assert req.path == "a.txt"

def test_remove_host_side():
    handler = make_handler()
    req = handler.remove("/host/file.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False
    assert req.dst_path is None

def test_copytree_in_container():
    handler = make_handler()
    req = handler.copytree("dir1", "dir2")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE
    assert req.path == "dir1"
    assert req.dst_path == "dir2"

def test_copytree_host_to_container_and_reverse():
    handler = make_handler()
    handler.const_handler.workspace_path = "/workspace"
    req = handler.copytree("/host/dir1", "in_container_dir")
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == "/host/dir1"
    assert req.dst_path == "in_container_dir"
    assert req.container == "test_container"
    assert req.to_container is True

def test_rmtree_in_container():
    handler = make_handler()
    req = handler.rmtree("dir1")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE
    assert req.path == "dir1"

def test_rmtree_host_side():
    handler = make_handler()
    req = handler.rmtree("/host/dir1")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False
    assert req.dst_path is None 