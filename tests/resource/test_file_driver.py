import pytest
from src.operations.file.file_driver import FileDriver
import tempfile
import os
from pathlib import Path

class DummyFileDriver(FileDriver):
    def _move_impl(self, src_path, dst_path):
        raise NotImplementedError
    
    def _copy_impl(self, src_path, dst_path):
        raise NotImplementedError
    
    def _exists_impl(self, path):
        raise NotImplementedError
    
    def _create_impl(self, path, content):
        raise NotImplementedError
    
    def _copytree_impl(self, src_path, dst_path):
        raise NotImplementedError
    
    def _rmtree_impl(self, path):
        raise NotImplementedError
    
    def _remove_impl(self, path):
        raise NotImplementedError
    
    def open(self, path, mode="r", encoding=None):
        pass
    
    def docker_cp(self, src, dst, container, to_container=True, docker_driver=None):
        pass
    
    def list_files(self, base_dir):
        return []

def test_move_impl_not_implemented():
    driver = DummyFileDriver()
    src_path = driver.base_dir / "a.txt"
    dst_path = driver.base_dir / "b.txt"
    with pytest.raises(NotImplementedError):
        driver._move_impl(src_path, dst_path)

def test_copy_impl_not_implemented():
    driver = DummyFileDriver()
    src_path = driver.base_dir / "a.txt"
    dst_path = driver.base_dir / "b.txt"
    with pytest.raises(NotImplementedError):
        driver._copy_impl(src_path, dst_path)

def test_exists_impl_not_implemented():
    driver = DummyFileDriver()
    path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._exists_impl(path)

def test_create_impl_not_implemented():
    driver = DummyFileDriver()
    path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._create_impl(path, "")

def test_copytree_impl_not_implemented():
    driver = DummyFileDriver()
    src_path = driver.base_dir / "a.txt"
    dst_path = driver.base_dir / "b.txt"
    with pytest.raises(NotImplementedError):
        driver._copytree_impl(src_path, dst_path)

def test_rmtree_impl_not_implemented():
    driver = DummyFileDriver()
    path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._rmtree_impl(path)

def test_remove_impl_not_implemented():
    driver = DummyFileDriver()
    path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._remove_impl(path)

def test_copytree_src_equals_dst():
    driver = DummyFileDriver()
    src_path = "a.txt"
    dst_path = "a.txt"
    # _copytree_implは呼ばれないのでNotImplementedErrorは出ない
    driver.copytree(src_path, dst_path)

def test_filedriver_hash_file_and_ensure_parent_dir():
    driver = DummyFileDriver()
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.txt")
        driver.ensure_parent_dir(file_path)
        with open(file_path, "w") as f:
            f.write("abc")
        # 相対パスを作成してテスト
        rel_path = os.path.relpath(file_path, driver.base_dir)
        h = driver.hash_file(rel_path)
        assert isinstance(h, str) and len(h) > 0

def test_filedriver_glob_isdir_makedirs():
    driver = DummyFileDriver(base_dir=Path("."))
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = os.path.join(tmpdir, "subdir")
        rel_subdir = os.path.relpath(subdir, driver.base_dir)
        driver.makedirs(rel_subdir)
        assert driver.isdir(rel_subdir)
        files = driver.glob("*")
        assert isinstance(files, list)

def test_list_files_local_file_driver(tmp_path):
    # ディレクトリ・ファイル構成を作成
    (tmp_path / "a").mkdir()
    (tmp_path / "a" / "b").mkdir()
    (tmp_path / "a" / "b" / "file1.txt").write_text("hello")
    (tmp_path / "a" / "file2.txt").write_text("world")
    from src.operations.file.local_file_driver import LocalFileDriver
    driver = LocalFileDriver(base_dir=tmp_path)
    files = set(driver.list_files("a"))
    expected = {
        str(tmp_path / "a" / "b" / "file1.txt"),
        str(tmp_path / "a" / "file2.txt"),
    }
    assert files == expected

def test_list_files_mock_file_driver():
    from src.operations.mock.mock_file_driver import MockFileDriver
    from pathlib import Path
    driver = MockFileDriver(base_dir=Path("."))
    # 仮想ファイルを追加
    driver.add("a/b/file1.txt", "hello")
    driver.add("a/file2.txt", "world")
    files = set(driver.list_files("a"))
    expected = {Path("a/b/file1.txt"), Path("a/file2.txt")}
    assert files == expected 