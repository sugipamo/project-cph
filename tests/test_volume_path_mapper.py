from pathlib import Path
from src.path_manager.volume_path_mapper import VolumePathMapper
import os

def test_single_mount():
    host = Path("/tmp/host")
    cont = Path("/workspace/host")
    vpm = VolumePathMapper([(host, cont)])
    assert vpm.to_container_path(host / "a.txt") == cont / "a.txt"
    assert vpm.to_host_path(cont / "a.txt") == host / "a.txt"
    # 未マウント領域
    assert vpm.to_container_path(Path("/tmp/other/b.txt")) is None
    assert vpm.to_host_path(Path("/workspace/other/b.txt")) is None

def test_multiple_mounts():
    vpm = VolumePathMapper([
        (Path("/tmp/host1"), Path("/workspace/h1")),
        (Path("/tmp/host2"), Path("/workspace/h2")),
    ])
    assert vpm.to_container_path(Path("/tmp/host1/foo.txt")) == Path("/workspace/h1/foo.txt")
    assert vpm.to_container_path(Path("/tmp/host2/bar.txt")) == Path("/workspace/h2/bar.txt")
    assert vpm.to_container_path(Path("/tmp/other/baz.txt")) is None

def test_add_mount():
    vpm = VolumePathMapper([])
    vpm.add_mount(Path("/tmp/abc"), Path("/workspace/abc"))
    assert vpm.to_container_path(Path("/tmp/abc/x.txt")) == Path("/workspace/abc/x.txt")

def test_from_required_paths_common():
    # 共通親が/tmp/data
    paths = [Path("/tmp/data/a.txt"), Path("/tmp/data/b/c.txt")]
    vpm = VolumePathMapper.from_required_paths(paths, Path("/workspace"))
    # /workspace/data/xxx になる
    assert vpm.to_container_path(Path("/tmp/data/a.txt")) == Path("/workspace/data/a.txt")
    assert vpm.to_container_path(Path("/tmp/data/b/c.txt")) == Path("/workspace/data/b/c.txt")
    # 未マウント
    assert vpm.to_container_path(Path("/tmp/other.txt")) is None

def test_get_mounts():
    host = Path("/tmp/host")
    cont = Path("/workspace/host")
    vpm = VolumePathMapper([(host, cont)])
    mounts = vpm.get_mounts()
    assert len(mounts) == 1
    assert mounts[0][0] == host.resolve()
    assert mounts[0][1] == cont 