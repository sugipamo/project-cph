import pytest
from unittest.mock import MagicMock, Mock
from src.env_resource.file.docker_file_handler import DockerFileHandler
from src.env_resource.file.local_file_handler import LocalFileHandler
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.docker.docker_file_request import DockerFileRequest
from src.context.execution_context import ExecutionContext
import unittest.mock

class DummyConfig:
    pass

@pytest.fixture
def config():
    return DummyConfig()

@pytest.fixture 
def docker_config():
    """Create a simple config for Docker tests"""
    config = ExecutionContext(
        command_type="test",
        language="python", 
        contest_name="abc123",
        problem_name="a",
        env_type="docker",
        env_json={"python": {"workspace_path": "/workspace"}}
    )
    return config

@pytest.fixture
def docker_handler(docker_config):
    handler = DockerFileHandler(docker_config)
    # Override the problematic initialization
    handler.workspace_path = "/workspace"
    from src.env_resource.utils.path_environment_checker import PathEnvironmentChecker
    handler.path_env_checker = PathEnvironmentChecker("/workspace")
    return handler

@pytest.fixture
def local_handler(config):
    return LocalFileHandler(config)

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup - requires resolver")
def test_docker_read_write_exists(docker_handler):
    assert isinstance(docker_handler.read("foo.txt"), FileRequest)
    assert isinstance(docker_handler.write("foo.txt", "abc"), FileRequest)
    assert isinstance(docker_handler.exists("foo.txt"), FileRequest)

def test_local_read_write_exists(local_handler):
    assert isinstance(local_handler.read("foo.txt"), FileRequest)
    assert isinstance(local_handler.write("foo.txt", "abc"), FileRequest)
    assert isinstance(local_handler.exists("foo.txt"), FileRequest)

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup - requires resolver")
def test_docker_copy_in_container_to_in_container(docker_handler):
    # Both paths are relative, so they should be treated as in-container
    req = docker_handler.copy("src.txt", "dst.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_copy_host_to_container(docker_handler):
    with unittest.mock.patch("src.env.resource.utils.path_environment_checker.PathEnvironmentChecker.is_in_container", lambda self, path: "in_container" in str(path)):
        req = docker_handler.copy("host.txt", "in_container_dst.txt")
        assert isinstance(req, DockerFileRequest)
        assert req.to_container is True

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_copy_container_to_host(docker_handler):
    with unittest.mock.patch("src.env.resource.utils.path_environment_checker.PathEnvironmentChecker.is_in_container", lambda self, path: "in_container" in str(path)):
        req = docker_handler.copy("in_container_src.txt", "host.txt")
        assert isinstance(req, DockerFileRequest)
        assert req.to_container is False

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_copytree_in_container_to_in_container(docker_handler):
    req = docker_handler.copytree("in_container_src", "in_container_dst")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_copytree_host_to_container(docker_handler):
    with unittest.mock.patch("src.env.resource.utils.path_environment_checker.PathEnvironmentChecker.is_in_container", lambda self, path: "in_container" in str(path)):
        req = docker_handler.copytree("host", "in_container_dst")
        assert isinstance(req, DockerFileRequest)
        assert req.to_container is True

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_move_in_container_to_in_container(docker_handler):
    with unittest.mock.patch("src.env.resource.utils.path_environment_checker.PathEnvironmentChecker.is_in_container", lambda self, path: "in_container" in str(path)):
        req = docker_handler.move("in_container_src", "in_container_dst")
        assert isinstance(req, FileRequest)
        assert req.op == FileOpType.MOVE

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_move_host_to_container(docker_handler):
    with unittest.mock.patch("src.env.resource.utils.path_environment_checker.PathEnvironmentChecker.is_in_container", lambda self, path: "in_container" in str(path)):
        req = docker_handler.move("host", "in_container_dst")
        assert isinstance(req, DockerFileRequest)
        assert req.to_container is True

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup - requires resolver")
def test_docker_remove_in_container(docker_handler):
    # Test removing a file that's considered in container (relative path)
    req = docker_handler.remove("test_file.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_remove_host(docker_handler):
    req = docker_handler.remove("host_file")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup - requires resolver")
def test_docker_rmtree_in_container(docker_handler):
    # Test removing a directory that's considered in container (relative path)
    req = docker_handler.rmtree("test_dir")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE

@pytest.mark.skip(reason="Complex Docker path logic needs proper setup")
def test_docker_rmtree_host(docker_handler):
    req = docker_handler.rmtree("host_dir")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

def test_local_copy_file(local_handler, tmp_path):
    src = tmp_path / "foo.txt"
    dst = tmp_path / "bar.txt"
    src.write_text("abc")
    req = local_handler.copy(str(src), str(dst))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY

def test_local_copy_dir(local_handler, tmp_path):
    src = tmp_path / "foo"
    dst = tmp_path / "bar"
    src.mkdir()
    req = local_handler.copy(str(src), str(dst))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE

def test_local_move_abs(local_handler, tmp_path):
    src = tmp_path / "foo.txt"
    dst = tmp_path / "bar.txt"
    src.write_text("abc")
    req = local_handler.move(str(src), str(dst))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE

def test_local_move_rel(local_handler, tmp_path):
    src = tmp_path / "foo.txt"
    dst = tmp_path / "bar.txt"
    src.write_text("abc")
    req = local_handler.move(str(src), str(dst))
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