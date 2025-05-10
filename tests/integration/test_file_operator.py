from pathlib import Path
from src.file.file_operator import MockFileOperator
from src.file.file_operator import LocalFileOperator
import os
import pytest
import shutil
from src.file.file_operator import FileOperator

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

def test_localfileoperator_remove_oserror(tmp_path, monkeypatch):
    op = LocalFileOperator(tmp_path)
    f = tmp_path / "f.txt"
    f.write_text("x")
    def raise_perm(self, *a, **k):
        raise PermissionError("denied")
    monkeypatch.setattr("pathlib.Path.unlink", raise_perm)
    with pytest.raises(PermissionError):
        op.remove(f)

def test_localfileoperator_rmtree_oserror(tmp_path):
    op = LocalFileOperator(tmp_path)
    d = tmp_path / "d"
    d.mkdir()
    import shutil as orig_shutil
    orig_rmtree = orig_shutil.rmtree
    def raise_oserr(*a, **k):
        raise OSError("fail")
    orig_shutil.rmtree = raise_oserr
    with pytest.raises(OSError):
        op.rmtree(d)
    orig_shutil.rmtree = orig_rmtree

def test_localfileoperator_copytree_oserror(tmp_path):
    op = LocalFileOperator(tmp_path)
    src = tmp_path / "src"
    dst = tmp_path / "dst"
    src.mkdir()
    import shutil as orig_shutil
    orig_copytree = orig_shutil.copytree
    def raise_oserr(*a, **k):
        raise OSError("fail")
    orig_shutil.copytree = raise_oserr
    with pytest.raises(OSError):
        op.copytree(src, dst)
    orig_shutil.copytree = orig_copytree

def test_localfileoperator_open_notfound(tmp_path):
    op = LocalFileOperator(tmp_path)
    f = tmp_path / "no.txt"
    with pytest.raises(FileNotFoundError):
        with op.open(f, "r"): pass

def test_localfileoperator_makedirs_permission(tmp_path):
    op = LocalFileOperator(tmp_path)
    d = tmp_path / "d"
    import pathlib
    orig_mkdir = pathlib.Path.mkdir
    def raise_perm(*a, **k):
        raise PermissionError("denied")
    pathlib.Path.mkdir = raise_perm
    with pytest.raises(PermissionError):
        op.makedirs(d)
    pathlib.Path.mkdir = orig_mkdir

def test_localfileoperator_isdir_and_glob(tmp_path):
    op = LocalFileOperator(tmp_path)
    d = tmp_path / "d"
    d.mkdir()
    f = d / "a.txt"
    f.write_text("x")
    assert op.isdir(d)
    assert not op.isdir(tmp_path / "no")
    # globで一致しないパターン
    assert op.glob("no.txt") == []
    # globで一致するパターン
    assert op.glob("d/*.txt") == [f]

def test_resolve_path_variants(tmp_path):
    op = LocalFileOperator(tmp_path)
    # str型
    assert op.resolve_path("foo.txt") == tmp_path / "foo.txt"
    # Path型
    assert op.resolve_path(Path("bar.txt")) == tmp_path / "bar.txt"
    # すでに絶対パス
    abs_path = tmp_path / "abs.txt"
    assert op.resolve_path(abs_path) == abs_path

def test_fileoperator_cannot_instantiate():
    with pytest.raises(TypeError):
        FileOperator()

def test_remove_nonexistent(tmp_path):
    op = LocalFileOperator(tmp_path)
    f = tmp_path / 'no.txt'
    # 存在しないファイルのremoveはFileNotFoundError
    with pytest.raises(FileNotFoundError):
        op.remove(f)

def test_rmtree_nonexistent(tmp_path):
    op = LocalFileOperator(tmp_path)
    d = tmp_path / 'no_dir'
    # 存在しないディレクトリのrmtreeは何も起きない（例外なし）
    op.rmtree(d)

def test_open_permission_error(tmp_path):
    op = LocalFileOperator(tmp_path)
    f = tmp_path / 'f.txt'
    f.write_text('x')
    os.chmod(f, 0o000)
    try:
        with pytest.raises(PermissionError):
            with op.open(f, 'r'): pass
    finally:
        os.chmod(f, 0o644)

def test_makedirs_already_exists(tmp_path):
    op = LocalFileOperator(tmp_path)
    d = tmp_path / 'd'
    d.mkdir()
    # 既に存在していても例外は出ない
    op.makedirs(d)

def test_glob_subdir(tmp_path):
    op = LocalFileOperator(tmp_path)
    d = tmp_path / 'd'
    d.mkdir()
    (d / 'a.txt').write_text('x')
    (d / 'b.py').write_text('y')
    # サブディレクトリ内の*.txtのみ
    assert op.glob('d/*.txt') == [d / 'a.txt']
    # ワイルドカードで全ファイル
    assert set(op.glob('d/*')) == {d / 'a.txt', d / 'b.py'} 