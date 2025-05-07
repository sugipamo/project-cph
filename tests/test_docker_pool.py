import pytest
from src.docker.pool import generate_container_name, DockerPool, DockerImageManager
import json

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
        self.started = []
        self.execs = []
        self.removed = []
    def is_container_running(self, name):
        return name in self._existing
    def start_container(self, name, typ, volumes):
        self.started.append((name, typ, volumes))
    def exec_in_container(self, name, cmd):
        self.execs.append((name, cmd))
        return True, "ok", ""
    def remove_container(self, name):
        self.removed.append(name)
    def list_cph_containers(self):
        return list(self._existing)


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
    started_names = [n for n, _, _ in ctl.started]
    assert "cph_test_python_1" in started_names
    assert "cph_test_python_2" in started_names
    assert "cph_ojtools_1" in started_names
    # containersリストの内容確認
    assert any(c["name"] == "cph_test_python_2" for c in containers)


def test_dockerpool_adjust_restarts_stopped():
    # 停止したコンテナを再起動するテスト
    class StoppedContainerCtl(DummyCtl):
        def is_container_running(self, name):
            # cph_test_python_1は停止中、cph_ojtools_1は実行中と仮定
            return name == "cph_ojtools_1"

    ctl = StoppedContainerCtl()
    ctl._existing = {"cph_test_python_1", "cph_ojtools_1"}
    pool = DockerPool()
    pool.ctl = ctl
    pool.image_manager = DockerImageManager()  # イメージマネージャーを設定

    requirements = [
        {"type": "test", "language": "python", "count": 1},
        {"type": "ojtools", "count": 1}
    ]
    containers = pool.adjust(requirements)

    # 停止中のコンテナは削除されて再作成される
    assert "cph_test_python_1" in ctl.removed
    assert "cph_ojtools_1" not in ctl.removed

    # 停止中のコンテナのみ再起動される
    assert len(ctl.started) == 1
    started_name, started_image, _ = ctl.started[0]
    assert started_name == "cph_test_python_1"

    # containersリストには両方含まれる
    assert any(c["name"] == "cph_test_python_1" for c in containers)
    assert any(c["name"] == "cph_ojtools_1" for c in containers)


def test_dockerpool_adjust_restarts_volume_changed():
    # ボリューム構成が変更された場合のテスト
    class VolumeInspectCtl(DummyCtl):
        def __init__(self):
            super().__init__()
            self.inspect_results = {}

        def is_container_running(self, name):
            return True

        def exec_in_container(self, name, cmd):
            if isinstance(cmd, list) and len(cmd) > 2 and cmd[0] == "docker" and cmd[1] == "inspect":
                container_name = cmd[-1]
                if container_name in self.inspect_results:
                    return True, self.inspect_results[container_name], ""
            return True, "[]", ""

    ctl = VolumeInspectCtl()
    ctl._existing = {"cph_test_python_1", "cph_ojtools_1"}
    # cph_test_python_1の既存ボリューム設定
    ctl.inspect_results["cph_test_python_1"] = json.dumps([
        {"Source": "/old/path", "Destination": "/workspace"}
    ])

    pool = DockerPool()
    pool.ctl = ctl
    pool.image_manager = DockerImageManager()  # イメージマネージャーを設定

    requirements = [
        {
            "type": "test", 
            "language": "python", 
            "count": 1,
            "volumes": {"/new/path": "/workspace"}
        },
        {"type": "ojtools", "count": 1}
    ]
    containers = pool.adjust(requirements)

    # ボリューム構成が異なるコンテナは削除されて再作成される
    assert "cph_test_python_1" in ctl.removed
    assert "cph_ojtools_1" not in ctl.removed

    # ボリューム構成が異なるコンテナのみ再起動される
    assert len(ctl.started) == 1
    started_name, started_image, started_volumes = ctl.started[0]
    assert started_name == "cph_test_python_1"
    assert started_volumes == {"/new/path": "/workspace"}

    # containersリストには両方含まれる
    assert any(c["name"] == "cph_test_python_1" for c in containers)
    assert any(c["name"] == "cph_ojtools_1" for c in containers) 