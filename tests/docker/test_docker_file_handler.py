import pytest
from src.env_resource.file.docker_file_handler import DockerFileHandler
from src.context.execution_context import ExecutionContext
from src.operations.file.file_request import FileRequest
from src.operations.file.file_op_type import FileOpType
from src.operations.docker.docker_file_request import DockerFileRequest
from src.operations.mock.mock_docker_driver import MockDockerDriver

pytestmark = pytest.mark.skip(reason="Docker file handler tests need path environment setup")

def make_docker_handler(ws):
    return DockerFileHandler({})

def test_copy_in_container(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = ws / "a.txt"
    dst = ws / "b.txt"
    src.touch()
    req = handler.copy(str(src), str(dst))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == str(src)
    assert req.dst_path == str(dst)

def test_copy_host_to_container(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = "/host/file.txt"
    dst = ws / "in_container.txt"
    req = handler.copy(src, str(dst))
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == src
    assert req.dst_path == str(dst)
    assert req.container == "test_container"
    assert req.to_container is True

def test_copy_container_to_host(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = ws / "in_container.txt"
    dst = "/host/file.txt"
    req = handler.copy(str(src), dst)
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == str(src)
    assert req.dst_path == dst
    assert req.container == "test_container"
    assert req.to_container is False

def test_move_in_container(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = ws / "a.txt"
    dst = ws / "b.txt"
    src.touch()
    req = handler.move(str(src), str(dst))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.MOVE
    assert req.path == str(src)
    assert req.dst_path == str(dst)

def test_move_host_to_container_and_reverse(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = "/host/file.txt"
    dst = ws / "in_container.txt"
    req = handler.move(src, str(dst))
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == src
    assert req.dst_path == str(dst)
    assert req.container == "test_container"
    assert req.to_container is True
    # 逆方向
    src2 = ws / "in_container.txt"
    dst2 = "/host/file.txt"
    req2 = handler.move(str(src2), dst2)
    assert isinstance(req2, DockerFileRequest)
    assert req2.src_path == str(src2)
    assert req2.dst_path == dst2
    assert req2.container == "test_container"
    assert req2.to_container is False

def test_remove_in_container(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    target = ws / "a.txt"
    target.touch()
    req = handler.remove(str(target))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.REMOVE
    assert req.path == str(target)

def test_remove_host_side(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    target = "/host/file.txt"
    req = handler.remove(target)
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False
    assert req.dst_path is None

def test_copytree_in_container(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = ws / "dir1"
    dst = ws / "dir2"
    src.mkdir()
    req = handler.copytree(str(src), str(dst))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPYTREE
    assert req.path == str(src)
    assert req.dst_path == str(dst)

def test_copytree_host_to_container_and_reverse(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = "/host/dir1"
    dst = ws / "in_container_dir"
    req = handler.copytree(src, str(dst))
    assert isinstance(req, DockerFileRequest)
    assert req.src_path == src
    assert req.dst_path == str(dst)
    assert req.container == "test_container"
    assert req.to_container is True
    # 逆方向
    src2 = ws / "in_container_dir"
    dst2 = "/host/dir1"
    req2 = handler.copytree(str(src2), dst2)
    assert isinstance(req2, DockerFileRequest)
    assert req2.src_path == str(src2)
    assert req2.dst_path == dst2
    assert req2.container == "test_container"
    assert req2.to_container is False

def test_rmtree_in_container(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    target = ws / "dir1"
    target.mkdir()
    req = handler.rmtree(str(target))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.RMTREE
    assert req.path == str(target)

def test_rmtree_host_side(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    target = "/host/dir1"
    req = handler.rmtree(target)
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False
    assert req.dst_path is None 