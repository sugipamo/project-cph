import pytest
from pathlib import Path
from src.infrastructure.mock.mock_file_driver import MockFileDriver

def test_create_and_exists():
    driver = MockFileDriver()
    p = Path("a.txt")
    assert not driver._exists_impl(p)
    driver._create_impl(p, "abc")
    assert driver._exists_impl(p)
    assert driver.contents[p] == "abc"

def test_behavior_verification():
    """MockFileDriverの振る舞い検証機能をテスト"""
    driver = MockFileDriver()
    
    # 操作を実行
    test_path = driver.base_dir / Path("test.txt")
    copy_path = driver.base_dir / Path("copy.txt")
    moved_path = driver.base_dir / Path("moved.txt")
    
    driver._create_impl(test_path, "content")
    driver._copy_impl(test_path, copy_path)
    driver._move_impl(copy_path, moved_path)
    
    # 振る舞い検証
    driver.assert_operation_called("create")
    driver.assert_operation_called("copy", times=1)
    driver.assert_operation_called("move", times=1)
    
    # 特定の引数での呼び出し検証
    driver.assert_operation_called_with("create", test_path, "content")

def test_file_exists_setup():
    """ファイル存在状態の設定機能をテスト"""
    driver = MockFileDriver()
    
    # ファイルの存在状態を設定
    driver.set_file_exists("existing_file.txt", exists=True)
    driver.set_file_exists("non_existing_file.txt", exists=False)
    
    # 確認
    assert driver._exists_impl(driver.base_dir / "existing_file.txt")
    assert not driver._exists_impl(driver.base_dir / "non_existing_file.txt")

def test_move_and_copy_impl():
    driver = MockFileDriver()
    src = driver.base_dir / Path("a.txt")
    dst = driver.base_dir / Path("b.txt")
    driver._create_impl(src, "abc")
    driver._move_impl(src, dst)
    assert not driver._exists_impl(src)
    assert driver._exists_impl(dst)
    driver._copy_impl(dst, src)
    assert driver._exists_impl(src)
    assert driver.contents[src] == "abc"

def test_copy_impl_file_not_found():
    driver = MockFileDriver()
    with pytest.raises(FileNotFoundError):
        driver._copy_impl(driver.base_dir / Path("notfound.txt"), driver.base_dir / Path("b.txt"))

def test_copytree_and_rmtree_impl():
    driver = MockFileDriver()
    src = driver.base_dir / Path("dir1")
    dst = driver.base_dir / Path("dir2")
    driver._create_impl(src, "")
    driver._copytree_impl(src, dst)
    assert ("copytree", src, dst) in driver.operations
    driver._rmtree_impl(src)
    assert not driver._exists_impl(src)

def test_remove_impl():
    driver = MockFileDriver()
    p = driver.base_dir / Path("a.txt")
    driver._create_impl(p, "abc")
    driver._remove_impl(p)
    assert not driver._exists_impl(p)

def test_open_read_and_write():
    driver = MockFileDriver(base_dir=Path(""))
    p = Path("a.txt")
    driver.path = p
    driver._create_impl(driver.base_dir / p, "abc")
    with driver.open("a.txt", "r") as f:
        content = f.read()
    assert content == "abc"
    driver.path = p
    with driver.open("a.txt", "w") as f:
        f.write("def")
    assert driver.contents[driver.base_dir / p] == "def"  # writeで内容が上書きされる

def test_open_unsupported_mode():
    driver = MockFileDriver()
    driver.path = Path("a.txt")
    with pytest.raises(NotImplementedError):
        with driver.open("a.txt", "x") as f:
            pass

def test_docker_cp_and_hash_file():
    driver = MockFileDriver()
    p = driver.base_dir / Path("a.txt")
    driver._create_impl(p, "abc")
    driver.files.add(p)
    result = driver.docker_cp(str(p), "dst", "container")
    assert result.startswith("mock_docker_cp_")
    h = driver.hash_file(p)
    assert isinstance(h, str) and len(h) > 0
    # docker_cpでFileNotFoundError
    with pytest.raises(FileNotFoundError):
        driver.docker_cp("notfound.txt", "dst", "container") 