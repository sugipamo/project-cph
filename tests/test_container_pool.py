import pytest
from unittest.mock import MagicMock
from src.execution_client.container.pool import ContainerPool
from execution_client.container.client import AbstractContainerClient
from src.execution_client.container.image_manager import AbstractContainerImageManager

class DummyClient(AbstractContainerClient):
    def __init__(self):
        self.containers = set()
        self.running = set()
        self.removed = set()
        self.started = set()
        self.inspected = {}
    def run_container(self, name, image, **kwargs):
        self.containers.add(name)
        self.running.add(name)
        self.started.add(name)
        return name
    def stop_container(self, name):
        self.running.discard(name)
        return True
    def remove_container(self, name):
        self.containers.discard(name)
        self.running.discard(name)
        self.removed.add(name)
        return True
    def exec_in_container(self, name, cmd, **kwargs):
        return MagicMock(returncode=0, stdout="", stderr="")
    def copy_to_container(self, name, src_path, dst_path):
        return True
    def copy_from_container(self, name, src_path, dst_path):
        return True
    def is_container_running(self, name):
        return name in self.running
    def list_containers(self, all=True, prefix=None):
        if prefix:
            return [n for n in self.containers if n.startswith(prefix)]
        return list(self.containers)
    def inspect_container(self, name):
        return self.inspected.get(name, {"Mounts": []})

class DummyImageManager(AbstractContainerImageManager):
    def __init__(self):
        self.ensured = set()
    def build_image(self, dockerfile_path, image_name, context_dir="."):
        return True
    def remove_image(self, image_name):
        return True
    def image_exists(self, image_name):
        return True
    def get_image_name(self, base_name, tag=None):
        return f"img_{base_name}"
    def get_dockerfile_hash(self, dockerfile_path):
        return "dummyhash"
    def cleanup_old_images(self, key):
        pass
    def ensure_image(self, key, context_dir="."):
        self.ensured.add(key)
        return f"img_{key}"

@pytest.fixture
def pool_with_dummy(monkeypatch):
    # ContainerPoolの内部client/image_managerをダミーに差し替え
    from src.execution_client.container.pool import ContainerPool
    pool = ContainerPool(dockerfile_map={"python": "dummy"})
    pool.client = DummyClient()
    pool.image_manager = DummyImageManager()
    return pool

def test_adjust_starts_and_removes(pool_with_dummy):
    pool = pool_with_dummy
    pool.client.containers = {"cph_test_python_1"}
    pool.client.running = {"cph_test_python_1"}
    requirements = [
        {"type": "test", "language": "python", "count": 2}
    ]
    result = pool.adjust(requirements)
    names = [c["name"] for c in result]
    # 必要な2つが最終的に存在していること
    assert set(names) == {"cph_test_python_1", "cph_test_python_2"}
    assert set(names) == set(pool.client.containers)
    # removedには余計なものが含まれていないこと（このケースでは、必要なもの以外が含まれていないこと）
    assert all(name in {"cph_test_python_1", "cph_test_python_2"} for name in pool.client.containers)

def test_adjust_removes_extra(pool_with_dummy):
    pool = pool_with_dummy
    pool.client.containers = {"cph_test_python_1", "cph_test_python_2", "cph_test_python_3"}
    pool.client.running = {"cph_test_python_1", "cph_test_python_2", "cph_test_python_3"}
    requirements = [
        {"type": "test", "language": "python", "count": 2}
    ]
    result = pool.adjust(requirements)
    names = [c["name"] for c in result]
    # 必要な2つが最終的に存在していること
    assert set(names) == {"cph_test_python_1", "cph_test_python_2"}
    assert set(names) == set(pool.client.containers)
    # removedには「余計なもの」が含まれていること（cph_test_python_3が含まれていること）
    assert "cph_test_python_3" in pool.client.removed 