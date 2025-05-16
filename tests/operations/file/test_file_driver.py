import os
import shutil
import tempfile
from pathlib import Path
import pytest
from src.operations.file.file_driver import LocalFileDriver, MockFileDriver, DummyFileDriver

def test_localfiledriver_create_and_exists(tmp_path):
    driver = LocalFileDriver(base_dir=tmp_path)
    driver.path = tmp_path / "test.txt"
    driver.create("hello")
    assert driver.exists()
    with driver.open("r", encoding="utf-8") as f:
        assert f.read() == "hello"

def test_localfiledriver_move_and_copy(tmp_path):
    driver = LocalFileDriver(base_dir=tmp_path)
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    driver.path = src
    driver.create("data")
    driver.path = src
    driver.dst_path = dst
    driver.move()
    assert not src.exists()
    assert dst.exists()
    driver.path = dst
    driver.dst_path = src
    driver.copy()
    assert src.exists()

def test_localfiledriver_copytree_and_rmtree(tmp_path):
    src_dir = tmp_path / "srcdir"
    dst_dir = tmp_path / "dstdir"
    src_dir.mkdir()
    (src_dir / "a.txt").write_text("A")
    driver = LocalFileDriver(base_dir=tmp_path)
    driver.path = src_dir
    driver.dst_path = dst_dir
    driver.copytree()
    assert (dst_dir / "a.txt").exists()
    driver.path = dst_dir
    driver.rmtree()
    assert not dst_dir.exists()

def test_mockfiledriver_operations():
    driver = MockFileDriver()
    driver.path = Path("foo.txt")
    driver.create("bar")
    assert driver.exists()
    driver.dst_path = Path("foo2.txt")
    driver.copy()
    assert driver.exists()
    driver.path = Path("foo2.txt")
    driver.dst_path = Path("foo3.txt")
    driver.move()
    try:
        driver.rmtree()
    except Exception:
        pass

def test_dummyfiledriver_operations():
    driver = DummyFileDriver()
    driver.path = Path("foo.txt")
    driver.create("bar")
    assert driver.exists()
    driver.dst_path = Path("foo2.txt")
    driver.copy()
    driver.path = Path("foo2.txt")
    driver.dst_path = Path("foo3.txt")
    driver.move()
    driver.rmtree() 