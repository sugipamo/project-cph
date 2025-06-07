import pytest
import tempfile
import os
from pathlib import Path
from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver


def test_move_and_copy_impl(tmp_path):
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.txt"
    src.write_text("abc")
    driver = LocalFileDriver()
    driver.path = src
    driver.dst_path = dst
    driver._move_impl(src, dst)
    assert dst.exists() and not src.exists()
    dst2 = tmp_path / "c.txt"
    driver._copy_impl(dst, dst2)
    assert dst2.exists()

def test_exists_and_create_impl(tmp_path):
    p = tmp_path / "a.txt"
    driver = LocalFileDriver()
    driver.path = p
    assert not driver._exists_impl(p)
    driver._create_impl(p, "hello")
    assert driver._exists_impl(p)
    assert p.read_text() == "hello"

def test_copytree_and_rmtree_impl(tmp_path):
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    (src_dir / "f.txt").write_text("x")
    driver = LocalFileDriver()
    driver._copytree_impl(src_dir, dst_dir)
    assert (dst_dir / "f.txt").exists()
    driver._rmtree_impl(dst_dir)
    assert not dst_dir.exists()

def test_remove_impl(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("x")
    driver = LocalFileDriver()
    driver._remove_impl(p)
    assert not p.exists()

def test_open(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("abc")
    driver = LocalFileDriver()
    driver.path = p
    with driver.open(p, "r") as f:
        assert f.read() == "abc"

def test_docker_cp_raises():
    driver = LocalFileDriver()
    with pytest.raises(ValueError):
        driver.docker_cp("src", "dst", "container")

def test_hash_file(tmp_path):
    p = tmp_path / "a.txt"
    p.write_text("abc")
    driver = LocalFileDriver()
    h = driver.hash_file(p)
    assert isinstance(h, str) and len(h) > 0 