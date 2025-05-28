import pytest
from src.operations.file.file_driver import FileDriver, FileUtil
import tempfile
import os
from pathlib import Path

class DummyFileDriver(FileDriver):
    def open(self, mode="r", encoding=None):
        pass
    def docker_cp(self, src, dst, container, to_container=True, docker_driver=None):
        pass

def test_move_impl_not_implemented():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    driver.dst_path = driver.base_dir / "b.txt"
    with pytest.raises(NotImplementedError):
        driver._move_impl(driver.path, driver.dst_path)

def test_copy_impl_not_implemented():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    driver.dst_path = driver.base_dir / "b.txt"
    with pytest.raises(NotImplementedError):
        driver._copy_impl(driver.path, driver.dst_path)

def test_exists_impl_not_implemented():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._exists_impl(driver.path)

def test_create_impl_not_implemented():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._create_impl(driver.path, "")

def test_copytree_impl_not_implemented():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    driver.dst_path = driver.base_dir / "b.txt"
    with pytest.raises(NotImplementedError):
        driver._copytree_impl(driver.path, driver.dst_path)

def test_rmtree_impl_not_implemented():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._rmtree_impl(driver.path)

def test_remove_impl_not_implemented():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    with pytest.raises(NotImplementedError):
        driver._remove_impl(driver.path)

def test_copytree_src_equals_dst():
    driver = DummyFileDriver()
    driver.path = driver.base_dir / "a.txt"
    driver.dst_path = driver.base_dir / "a.txt"
    # _copytree_implは呼ばれないのでNotImplementedErrorは出ない
    driver.copytree()

def test_fileutil_hash_file_and_ensure_parent_dir():
    with tempfile.TemporaryDirectory() as tmpdir:
        file_path = os.path.join(tmpdir, "test.txt")
        FileUtil.ensure_parent_dir(file_path)
        with open(file_path, "w") as f:
            f.write("abc")
        h = FileUtil.hash_file(file_path)
        assert isinstance(h, str) and len(h) > 0

def test_fileutil_glob_isdir_makedirs():
    with tempfile.TemporaryDirectory() as tmpdir:
        subdir = os.path.join(tmpdir, "subdir")
        FileUtil.makedirs(Path(subdir))
        assert FileUtil.isdir(Path(subdir))
        files = FileUtil.glob(Path(tmpdir), "*")
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
    driver.contents[Path("a/b/file1.txt")] = "hello"
    driver.contents[Path("a/file2.txt")] = "world"
    files = set(driver.list_files("a"))
    expected = {"a/b/file1.txt", "a/file2.txt"}
    assert files == expected 