import pytest
from pathlib import Path
from src.operations.mock.dummy_file_driver import DummyFileDriver

def test_dummy_file_driver_basic_operations():
    """DummyFileDriverは何もしない/エラーを起こさないことをテスト"""
    driver = DummyFileDriver()
    p = Path("a.txt")
    
    # 全ての操作がエラーを起こさないことを確認
    driver._create_impl(p, "abc")  # 何もしない
    driver._move_impl(p, Path("b.txt"))  # 何もしない
    driver._copy_impl(p, Path("c.txt"))  # 何もしない
    driver._rmtree_impl(p)  # 何もしない
    driver._remove_impl(p)  # 何もしない
    driver._copytree_impl(p, Path("d.txt"))  # 何もしない

def test_dummy_exists_always_false():
    """DummyFileDriverは常にFalseを返すことをテスト"""
    driver = DummyFileDriver()
    assert not driver._exists_impl(Path("a.txt"))
    assert not driver._exists_impl(Path("any_file"))

def test_dummy_open_returns_empty():
    """DummyFileDriverのopenは空のダミーオブジェクトを返すことをテスト"""
    driver = DummyFileDriver()
    
    with driver.open("a.txt", "r") as f:
        assert f.read() == ""
    
    with driver.open("a.txt", "w") as f:
        f.write("anything")  # 何もしない

def test_dummy_list_files_empty():
    """DummyFileDriverのlist_filesは空のリストを返すことをテスト"""
    driver = DummyFileDriver()
    assert driver.list_files("any_dir") == []

def test_dummy_docker_cp_does_nothing():
    """DummyFileDriverのdocker_cpは何もしないことをテスト"""
    driver = DummyFileDriver()
    # エラーを起こさないことを確認
    driver.docker_cp("src", "dst", "container")

def test_dummy_no_internal_state():
    """DummyFileDriverは内部状態を持たないことを確認"""
    driver = DummyFileDriver()
    
    # 内部状態関連の属性が存在しないことを確認
    assert not hasattr(driver, 'operations')
    assert not hasattr(driver, 'files')
    assert not hasattr(driver, 'contents') 