from pathlib import Path
from src.file_operator import MockFileOperator
from src.file_operator import LocalFileOperator
import os
import pytest

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