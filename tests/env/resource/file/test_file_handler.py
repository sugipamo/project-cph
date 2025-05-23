import pytest
from unittest.mock import MagicMock
from src.env.resource.file.file_handler import DockerFileHandler, LocalFileHandler
from src.operations.file.file_request import FileOpType, FileRequest
from src.operations.docker.docker_file_request import DockerFileRequest

class DummyConstHandler:
    workspace_path = "/ws"
    container_name = "cont"

class DummyConfig:
    pass

@pytest.fixture
def const_handler():
    return DummyConstHandler()

@pytest.fixture
def config():
    return DummyConfig()

@pytest.fixture
def docker_handler(config, const_handler, monkeypatch):
    # PathEnvironmentCheckerのis_in_containerをモック
    monkeypatch.setattr(
        "src.env.resource.utils.path_environment_checker.PathEnvironmentChecker.is_in_container",
        lambda self, path: "in_container" in str(path)
    )
    return DockerFileHandler(config, const_handler)

@pytest.fixture
def local_handler(config, const_handler):
    return LocalFileHandler(config, const_handler)

def test_docker_read_write_exists(docker_handler):
    assert isinstance(docker_handler.read("foo.txt"), FileRequest)
    assert isinstance(docker_handler.write("foo.txt", "abc"), FileRequest)
    assert isinstance(docker_handler.exists("foo.txt"), FileRequest)

def test_local_read_write_exists(local_handler):
    assert isinstance(local_handler.read("foo.txt"), FileRequest)
    assert isinstance(local_handler.write("foo.txt", "abc"), FileRequest)
    assert isinstance(local_handler.exists("foo.txt"), FileRequest)

def test_docker_copy_in_container_to_in_container(docker_handler):
    req = docker_handler.copy("in_container_src.txt", "in_container_dst.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY

def test_docker_copy_host_to_container(docker_handler):
    req = docker_handler.copy("host.txt", "in_container_dst.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True

def test_docker_copy_container_to_host(docker_handler):
    req = docker_handler.copy("in_container_src.txt", "host.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

def test_docker_copytree_in_container_to_in_container(docker_handler):
    req = docker_handler.copytree("in_container_src", "in_container_dst")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE

def test_docker_copytree_host_to_container(docker_handler):
    req = docker_handler.copytree("host", "in_container_dst")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True

def test_docker_move_in_container_to_in_container(docker_handler):
    req = docker_handler.move("in_container_src", "in_container_dst")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE

def test_docker_move_host_to_container(docker_handler):
    req = docker_handler.move("host", "in_container_dst")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True

def test_docker_remove_in_container(docker_handler):
    req = docker_handler.remove("in_container_file")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE

def test_docker_remove_host(docker_handler):
    req = docker_handler.remove("host_file")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

def test_docker_rmtree_in_container(docker_handler):
    req = docker_handler.rmtree("in_container_dir")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE

def test_docker_rmtree_host(docker_handler):
    req = docker_handler.rmtree("host_dir")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

def test_local_copy_file(monkeypatch, local_handler, const_handler):
    monkeypatch.setattr("os.path.isabs", lambda p: False)
    monkeypatch.setattr("os.path.isdir", lambda p: False)
    req = local_handler.copy("foo.txt", "bar.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY

def test_local_copy_dir(monkeypatch, local_handler, const_handler):
    monkeypatch.setattr("os.path.isabs", lambda p: False)
    monkeypatch.setattr("os.path.isdir", lambda p: True)
    req = local_handler.copy("foo", "bar")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE

def test_local_move_abs(monkeypatch, local_handler, const_handler):
    monkeypatch.setattr("os.path.isabs", lambda p: True)
    req = local_handler.move("/abs/foo", "bar")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE

def test_local_move_rel(monkeypatch, local_handler, const_handler):
    monkeypatch.setattr("os.path.isabs", lambda p: False)
    req = local_handler.move("foo", "bar")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE

def test_local_remove(local_handler):
    req = local_handler.remove("foo")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE

def test_local_copytree(local_handler):
    req = local_handler.copytree("foo", "bar")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE

def test_local_rmtree(local_handler):
    req = local_handler.rmtree("foo")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE 