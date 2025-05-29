import pytest
from pathlib import Path
from src.operations.mock.dummy_file_driver import DummyFileDriver

def test_create_and_exists():
    driver = DummyFileDriver()
    p = Path("a.txt")
    assert not driver._exists_impl(p)
    driver._create_impl(p, "abc")
    assert driver._exists_impl(p)
    assert driver.contents[p] == "abc"

def test_move_and_copy_impl():
    driver = DummyFileDriver()
    src = Path("a.txt")
    dst = Path("b.txt")
    driver._create_impl(src, "abc")
    driver._move_impl(src, dst)
    assert not driver._exists_impl(src)
    assert driver._exists_impl(dst)
    driver._copy_impl(dst, src)
    assert driver._exists_impl(src)
    assert driver.contents[src] == "abc"

def test_copytree_and_rmtree_impl():
    driver = DummyFileDriver()
    src = Path("dir1")
    dst = Path("dir2")
    driver._create_impl(src, "")
    driver._copytree_impl(src, dst)
    assert ("copytree", src, dst) in driver.operations
    driver._rmtree_impl(src)
    assert not driver._exists_impl(src)

def test_remove_impl():
    driver = DummyFileDriver()
    p = Path("a.txt")
    driver._create_impl(p, "abc")
    driver._remove_impl(p)
    assert not driver._exists_impl(p)

def test_isdir():
    driver = DummyFileDriver()
    driver.path = Path("dir/")
    assert not driver.isdir()
    driver.path = Path("file.txt")
    assert not driver.isdir()

def test_open_read_and_write():
    driver = DummyFileDriver()
    p = Path("a.txt")
    driver.path = p
    with driver.open("a.txt", "r") as f:
        assert f.read() == ""
    with driver.open("a.txt", "w") as f:
        f.write("def")

def test_ensure_parent_dir():
    driver = DummyFileDriver()
    p = Path("dir/a.txt")
    driver.ensure_parent_dir(p)
    assert Path("dir") in driver.files

def test_hash_file():
    driver = DummyFileDriver()
    p = Path("a.txt")
    driver._create_impl(p, "abc")
    h = driver.hash_file(p)
    assert h == "dummyhash" 