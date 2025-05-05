import pytest
from src.docker.pool import generate_container_name, DockerPool

# generate_container_nameのテスト
@pytest.mark.parametrize("purpose, language, index, expected", [
    ("test", "python", 1, "cph_test_python_1"),
    ("ojtools", None, 2, "cph_ojtools_2"),
    ("test", "rust", None, "cph_test_rust"),
])
def test_generate_container_name(purpose, language, index, expected):
    assert generate_container_name(purpose, language, index) == expected

# DockerPool.adjustのテスト
class DummyCtl:
    def __init__(self):
        self._existing = set()
        self.removed = []
        self.started = []
    def list_cph_containers(self):
        return list(self._existing)
    def remove_container(self, name):
        self.removed.append(name)
        self._existing.discard(name)
    def start_container(self, name, image):
        self.started.append((name, image))
        self._existing.add(name)


def test_dockerpool_adjust_removes_and_starts():
    ctl = DummyCtl()
    ctl._existing = {"cph_test_python_1", "cph_ojtools_1", "cph_old_1"}
    pool = DockerPool()
    pool.ctl = ctl  # 差し替え
    requirements = [
        {"type": "test", "language": "python", "count": 1},
        {"type": "ojtools", "count": 1}
    ]
    containers = pool.adjust(requirements)
    # cph_old_1がremoveされ、必要なものは残る
    assert "cph_old_1" in ctl.removed
    # 既存のものはremoveされない
    assert "cph_test_python_1" not in ctl.removed
    # startedに新規はない（全部既存）
    assert ctl.started == []
    # containersリストの内容確認
    assert any(c["name"] == "cph_test_python_1" for c in containers)
    assert any(c["name"] == "cph_ojtools_1" for c in containers)


def test_dockerpool_adjust_starts_missing():
    ctl = DummyCtl()
    ctl._existing = set()
    pool = DockerPool()
    pool.ctl = ctl
    requirements = [
        {"type": "test", "language": "python", "count": 2},
        {"type": "ojtools", "count": 1}
    ]
    containers = pool.adjust(requirements)
    # 3つ新規起動
    assert len(ctl.started) == 3
    started_names = [n for n, _ in ctl.started]
    assert "cph_test_python_1" in started_names
    assert "cph_test_python_2" in started_names
    assert "cph_ojtools_1" in started_names
    # containersリストの内容確認
    assert any(c["name"] == "cph_test_python_2" for c in containers) 