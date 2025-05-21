import pytest
from src.execution_env.resource_handler.file_handler.local_file_handler import LocalFileHandler
from src.execution_env.resource_handler.file_handler.docker_file_handler import DockerFileHandler
from src.operations.file.file_request import FileOpType, FileRequest
from src.operations.docker.docker_file_request import DockerFileRequest
from pathlib import Path

class DummyConstHandler:
    def __init__(self, workspace_path="/workspace", container_name="test_container"):
        self.workspace_path = workspace_path
        self._container_name = container_name
    @property
    def container_name(self):
        return self._container_name

def make_docker_handler(ws):
    return DockerFileHandler({}, DummyConstHandler(workspace_path=ws))

def test_is_in_container_true_false(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    (ws / "a.txt").touch()
    (ws / "dir").mkdir()
    (ws / "dir" / "b.txt").touch()
    # workspace内
    assert handler.path_env_checker.is_in_container(str(ws / "a.txt"))
    assert handler.path_env_checker.is_in_container(str(ws / "dir" / "b.txt"))
    # workspace外
    assert not handler.path_env_checker.is_in_container("/etc/passwd")
    assert not handler.path_env_checker.is_in_container(str(ws.parent / "outside.txt"))

def test_copy_host_to_container_and_reverse(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    # ホスト→コンテナ
    src = "/host/file.txt"
    dst = ws / "in_container.txt"
    req = handler.copy(src, str(dst))
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True
    # コンテナ→ホスト
    req2 = handler.copy(str(dst), src)
    assert isinstance(req2, DockerFileRequest)
    assert req2.to_container is False

def test_move_host_to_container_and_reverse(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = "/host/file.txt"
    dst = ws / "in_container.txt"
    req = handler.move(src, str(dst))
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True
    req2 = handler.move(str(dst), src)
    assert isinstance(req2, DockerFileRequest)
    assert req2.to_container is False

def test_remove_host_side():
    handler = make_docker_handler("/workspace")
    req = handler.remove("/host/file.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False
    assert req.dst_path is None

def test_rmtree_host_side():
    handler = make_docker_handler("/workspace")
    req = handler.rmtree("/host/dir1")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False
    assert req.dst_path is None

def test_copytree_host_to_container_and_reverse(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = "/host/dir1"
    dst = ws / "in_container_dir"
    req = handler.copytree(src, str(dst))
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True
    req2 = handler.copytree(str(dst), src)
    assert isinstance(req2, DockerFileRequest)
    assert req2.to_container is False

def test_invalid_path_edge_cases(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    # workspace直下
    file = ws / "file.txt"
    file.touch()
    assert handler.path_env_checker.is_in_container(str(file))
    # workspaceの親
    parent_file = ws.parent / "file.txt"
    assert not handler.path_env_checker.is_in_container(str(parent_file))
    # workspace自身
    assert handler.path_env_checker.is_in_container(str(ws))

def test_copy_within_workspace(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = ws / "foo.txt"
    dst = ws / "bar.txt"
    src.touch()
    req = handler.copy(str(src), str(dst))
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == str(src)
    assert req.dst_path == str(dst)

def test_copy_host_to_container_detect(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = "/host/file.txt"
    dst = ws / "bar.txt"
    req = handler.copy(src, str(dst))
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True

def test_copy_container_to_host_detect(tmp_path):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    src = ws / "foo.txt"
    dst = "/host/file.txt"
    req = handler.copy(str(src), dst)
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

@pytest.mark.parametrize("rel_path,expected", [
    ("a.txt", True),
    ("dir/b.txt", True),
    ("../outside.txt", False),
    ("", True),
])
def test_is_in_container_various(tmp_path, rel_path, expected):
    ws = tmp_path
    handler = make_docker_handler(str(ws))
    # 必要なファイル・ディレクトリを作成
    if rel_path:
        target = ws / rel_path
        target.parent.mkdir(parents=True, exist_ok=True)
        if not target.is_dir():
            target.touch()
        path = str(target)
    else:
        path = str(ws)
    assert handler.path_env_checker.is_in_container(path) == expected 