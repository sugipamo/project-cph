import os
import shutil
import json
from pathlib import Path
import pytest
from src.file.contest_file_manager import ContestFileManager
from src.file.file_operator import FileOperator
from src.file.file_operator import LocalFileOperator

class DummyFileOperator(FileOperator):
    def __init__(self, base_dir):
        self.base_dir = base_dir
    def copy(self, src, dst):
        pass
    def create(self, path, content=""):
        pass
    def exists(self, path):
        return False
    def move(self, src, dst):
        pass
    def copytree(self, src, dst):
        pass

@pytest.fixture
def temp_dirs(tmp_path):
    # テンプレートディレクトリとカレントディレクトリを作成
    template = tmp_path / "contest_template/python"
    template.mkdir(parents=True)
    (template / "main.py").write_text("print('hello')\n")
    current = tmp_path / "contest_current"
    current.mkdir(exist_ok=True)
    # 作業ディレクトリを一時ディレクトリに変更
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old_cwd)
    shutil.rmtree(tmp_path)

def test_problem_exists_in_stocks_and_current(temp_dirs):
    tmp_path = temp_dirs
    os.chdir(tmp_path)
    Path(tmp_path / "contest_current/system_info.json").write_text(json.dumps({
        "contest_name": "abc500",
        "problem_name": "e",
        "language_name": "python"
    }))
    manager = ContestFileManager(LocalFileOperator(base_dir=tmp_path))
    # stocksにmain.pyがある場合（pythonサブディレクトリに作成）
    stocks = tmp_path / "contest_stocks/abc500/e/python"
    stocks.mkdir(parents=True)
    (stocks / "main.py").write_text("print('exists')\n")
    assert manager.problem_exists_in_stocks("abc500", "e", "python") is True
    (stocks / "main.py").unlink()
    assert manager.problem_exists_in_stocks("abc500", "e", "python") is False
    current = tmp_path / "contest_current/python"
    current.mkdir(parents=True, exist_ok=True)
    (current / "main.py").write_text("print('exists')\n")
    assert manager.problem_exists_in_current("abc500", "e", "python") is True
    (current / "main.py").unlink()
    assert manager.problem_exists_in_current("abc500", "e", "python") is False

def test_is_ignored_regex(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = DummyFileOperator(base_dir=tmp_path)
    manager = ContestFileManager(op)
    # パターン一致
    assert manager._is_ignored("foo.log", [r"^foo\.log$"])
    # パターン不一致
    assert not manager._is_ignored("bar.txt", [r"^foo\.log$"])

def test_remove_empty_parents(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = DummyFileOperator(tmp_path)
    manager = ContestFileManager(op)
    base = tmp_path / "a" / "b" / "c"
    base.mkdir(parents=True)
    stop_at = tmp_path / "a"
    # c, bは空なので削除される
    manager._remove_empty_parents(base, stop_at)
    assert not (tmp_path / "a" / "b").exists()
    assert stop_at.exists()

def test_move_from_stocks_to_current_notfound(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = DummyFileOperator(tmp_path)
    manager = ContestFileManager(op)
    with pytest.raises(FileNotFoundError):
        manager.move_from_stocks_to_current("abc", "nope", "python")

def test_generate_moveignore_readme(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = DummyFileOperator(tmp_path)
    manager = ContestFileManager(op)
    # contest_currentディレクトリを作成
    (tmp_path / "contest_current").mkdir(parents=True, exist_ok=True)
    manager._generate_moveignore_readme()
    readme = tmp_path / "contest_current/README.md"
    assert readme.exists()
    assert "moveignore" in readme.read_text()

def test_stocks_exists_both_cases(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = LocalFileOperator(tmp_path)
    manager = ContestFileManager(op)
    lang_dir = tmp_path / 'contest_stocks/abc/z/python'
    test_dir = tmp_path / 'contest_stocks/abc/z/test'
    lang_dir.mkdir(parents=True)
    test_dir.mkdir(parents=True)
    (lang_dir / 'a.txt').write_text('a')
    (test_dir / 'b.txt').write_text('b')
    # lang_dirが非空
    assert manager.stocks_exists('abc', 'z', 'python')
    # lang_dirが空、test_dirが非空
    (lang_dir / 'a.txt').unlink()
    assert manager.stocks_exists('abc', 'z', 'python')
    # 両方空
    (test_dir / 'b.txt').unlink()
    assert not manager.stocks_exists('abc', 'z', 'python') 