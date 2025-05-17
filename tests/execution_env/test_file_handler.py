import pytest
from src.execution_env.resource_handler.file_handler import LocalFileHandler, DockerFileHandler
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

def make_docker_handler(ws="/workspace"):
    return DockerFileHandler({}, DummyConstHandler(workspace_path=ws))

def test_is_in_container_true_false():
    handler = make_docker_handler("/workspace")
    # workspace内
    assert handler._is_in_container("a.txt")
    assert handler._is_in_container("dir/b.txt")
    # workspace外
    assert not handler._is_in_container("/etc/passwd")
    assert not handler._is_in_container("../outside.txt")

def test_copy_host_to_container_and_reverse():
    handler = make_docker_handler("/workspace")
    # ホスト→コンテナ
    req = handler.copy("/host/file.txt", "in_container.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True
    # コンテナ→ホスト
    req = handler.copy("in_container.txt", "/host/file.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

def test_move_host_to_container_and_reverse():
    handler = make_docker_handler("/workspace")
    req = handler.move("/host/file.txt", "in_container.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True
    req = handler.move("in_container.txt", "/host/file.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

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

def test_copytree_host_to_container_and_reverse():
    handler = make_docker_handler("/workspace")
    req = handler.copytree("/host/dir1", "in_container_dir")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True
    req = handler.copytree("in_container_dir", "/host/dir1")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

def test_invalid_path_edge_cases():
    handler = make_docker_handler("/workspace")
    # workspace直下
    assert handler._is_in_container("/workspace/file.txt")
    # workspaceの親
    assert not handler._is_in_container("/workspace/../file.txt")
    # 空文字列
    assert handler._is_in_container("")
    # 絶対パスでworkspace内
    assert handler._is_in_container("/workspace/abc.txt")

def test_copy_within_workspace():
    handler = make_docker_handler("/workspace")
    req = handler.copy("foo.txt", "bar.txt")
    assert isinstance(req, FileRequest)
    assert req.op == FileOpType.COPY
    assert req.path == "foo.txt"
    assert req.dst_path == "bar.txt"

def test_copy_host_to_container_detect():
    handler = make_docker_handler("/workspace")
    req = handler.copy("/host/file.txt", "bar.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is True

def test_copy_container_to_host_detect():
    handler = make_docker_handler("/workspace")
    req = handler.copy("foo.txt", "/host/file.txt")
    assert isinstance(req, DockerFileRequest)
    assert req.to_container is False

@pytest.mark.parametrize("ws,path,expected", [
    ("/workspace", "a.txt", True),  # workspace直下
    ("/workspace", "dir/b.txt", True),  # workspace内サブディレクトリ
    ("/workspace", "/workspace/file.txt", True),  # 絶対パスでworkspace内
    ("/workspace", "/workspace/dir/c.txt", True),  # 絶対パスでサブディレクトリ
    ("/workspace", "../outside.txt", False),  # 親ディレクトリ参照
    ("/workspace", "/etc/passwd", False),  # 明らかに外
    ("/workspace", "/workspace/../file.txt", False),  # workspaceの親
    ("/workspace", "", True),  # 空文字列（=workspace自体）
    ("workspace", "a.txt", True),  # 相対workspace
    ("workspace", "../workspace/a.txt", False),  # 相対パスで外
])
def test_is_in_container_various(ws, path, expected):
    handler = make_docker_handler(ws)
    assert handler._is_in_container(path) == expected 