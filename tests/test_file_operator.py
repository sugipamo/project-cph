from pathlib import Path
from src.file_operator import MockFileOperator
from src.file_operator import LocalFileOperator
import os
import pytest
import shutil

def test_mockfileoperator_create_and_exists():
    op = MockFileOperator()
    p = Path("foo.txt")
    assert not op.exists(p)
    op.create(p, "hello")
    assert op.exists(p)
    assert op.contents[p] == "hello"

def test_mockfileoperator_copy():
    op = MockFileOperator()
    src = Path("src.txt")
    dst = Path("dst.txt")
    op.create(src, "abc")
    op.copy(src, dst)
    assert op.exists(dst)
    assert op.contents[dst] == "abc"
    # copy元は消えない
    assert op.exists(src)

def test_mockfileoperator_move():
    op = MockFileOperator()
    src = Path("src.txt")
    dst = Path("dst.txt")
    op.create(src, "xyz")
    op.move(src, dst)
    assert not op.exists(src)
    assert op.exists(dst)
    assert op.contents[dst] == "xyz"

def test_mockfileoperator_move_nonexistent():
    op = MockFileOperator()
    src = Path("no.txt")
    dst = Path("dst.txt")
    op.move(src, dst)  # 何も起きない
    assert not op.exists(dst)

def test_localfileoperator_create_and_exists(tmp_path):
    op = LocalFileOperator()
    p = tmp_path / "foo.txt"
    assert not op.exists(p)
    op.create(p, "hello")
    assert op.exists(p)
    assert p.read_text() == "hello"

def test_localfileoperator_copy(tmp_path):
    op = LocalFileOperator()
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    op.create(src, "abc")
    op.copy(src, dst)
    assert op.exists(dst)
    assert dst.read_text() == "abc"
    # copy元は消えない
    assert op.exists(src)

def test_localfileoperator_move(tmp_path):
    op = LocalFileOperator()
    src = tmp_path / "src.txt"
    dst = tmp_path / "dst.txt"
    op.create(src, "xyz")
    op.move(src, dst)
    assert not op.exists(src)
    assert op.exists(dst)
    assert dst.read_text() == "xyz"

def test_localfileoperator_move_nonexistent(tmp_path):
    op = LocalFileOperator()
    src = tmp_path / "no.txt"
    dst = tmp_path / "dst.txt"
    with pytest.raises(FileNotFoundError):
        op.move(src, dst)

def test_localfileoperator_copy_nonexistent(tmp_path):
    op = LocalFileOperator()
    src = tmp_path / "no.txt"
    dst = tmp_path / "dst.txt"
    with pytest.raises(FileNotFoundError):
        op.copy(src, dst)

def test_localfileoperator_create_overwrite(tmp_path):
    op = LocalFileOperator()
    p = tmp_path / "foo.txt"
    op.create(p, "first")
    assert p.read_text() == "first"
    op.create(p, "second")
    assert p.read_text() == "second"

def test_move_and_copy(tmp_path):
    op = LocalFileOperator(tmp_path)
    src = tmp_path / "a.txt"
    dst = tmp_path / "b.txt"
    src.write_text("hello")
    op.move(src, dst)
    assert dst.exists() and not src.exists()
    # copy
    dst2 = tmp_path / "c.txt"
    op.copy(dst, dst2)
    assert dst2.exists() and dst2.read_text() == "hello"

def test_exists_and_create(tmp_path):
    op = LocalFileOperator(tmp_path)
    f = tmp_path / "f.txt"
    assert not op.exists(f)
    op.create(f, "abc")
    assert op.exists(f)
    assert f.read_text() == "abc"

def test_copytree(tmp_path):
    op = LocalFileOperator(tmp_path)
    src_dir = tmp_path / "src"
    dst_dir = tmp_path / "dst"
    src_dir.mkdir()
    (src_dir / "a.txt").write_text("x")
    op.copytree(src_dir, dst_dir)
    assert (dst_dir / "a.txt").exists()
    # dirs_exist_ok=Trueなので再実行もOK
    op.copytree(src_dir, dst_dir)

def test_remove_and_rmtree(tmp_path):
    op = LocalFileOperator(tmp_path)
    f = tmp_path / "f.txt"
    d = tmp_path / "d"
    f.write_text("x")
    d.mkdir()
    (d / "a").write_text("y")
    op.remove(f)
    assert not f.exists()
    op.rmtree(d)
    assert not d.exists() 