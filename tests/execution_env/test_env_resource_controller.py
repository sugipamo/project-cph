import pytest
from src.execution_env.execution_env_registry import EnvResourceController, EnvType
from src.operations.file.file_request import FileOpType, FileRequest
from src.operations.docker.docker_file_request import DockerFileRequest
from src.execution_env.resource_handler.file_handler import LocalFileHandler, DockerFileHandler

class DummyConstHandler:
    @property
    def workspace(self):
        return "/workspace"
    @property
    def container_name(self):
        return "dummy_container"

def make_local_controller():
    file_handler = LocalFileHandler({}, DummyConstHandler())
    return EnvResourceController(env_config={}, file_handler=file_handler, run_handler=None, const_handler=None)

def make_docker_controller():
    file_handler = DockerFileHandler({}, DummyConstHandler())
    return EnvResourceController(env_config={}, file_handler=file_handler, run_handler=None, const_handler=None)

@pytest.mark.parametrize("controller, expected_handler_type", [
    (make_local_controller(), "LocalFileHandler"),
    (make_docker_controller(), "DockerFileHandler"),
])
def test_handler_switch(controller, expected_handler_type):
    assert controller.file_handler.__class__.__name__ == expected_handler_type

def test_local_file_handler_requests():
    controller = make_local_controller()
    req = controller.read_file("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.READ
    req = controller.copy_file("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    req = controller.move_file("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE
    req = controller.remove_file("a.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE
    req = controller.copytree("dir1", "dir2")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE
    req = controller.rmtree("dir1")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE

def test_docker_file_handler_requests():
    controller = make_docker_controller()
    req = controller.copy_file("a.txt", "b.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    req = controller.copy_file("/host/file.txt", "in_container.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == "/host/file.txt"
    assert req.dst_path == "in_container.txt"
    req = controller.copy_file("in_container.txt", "/host/file.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == "in_container.txt"
    assert req.dst_path == "/host/file.txt" 