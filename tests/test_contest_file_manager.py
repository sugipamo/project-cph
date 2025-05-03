import os
import shutil
import json
from pathlib import Path
import pytest
from src.contest_file_manager import ContestFileManager
from src.file_operator import FileOperator

class DummyFileOperator(FileOperator):
    def copy(self, src, dst):
        pass
    def create(self, path, content=""):
        pass
    def exists(self, path):
        return False
    def move(self, src, dst):
        pass

@pytest.fixture
def temp_dirs(tmp_path):
    # テンプレートディレクトリとカレントディレクトリを作成
    template = tmp_path / "contest_template/python"
    template.mkdir(parents=True)
    (template / "main.py").write_text("print('hello')\n")
    current = tmp_path / "contest_current"
    current.mkdir()
    # 作業ディレクトリを一時ディレクトリに変更
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    yield tmp_path
    os.chdir(old_cwd)
    shutil.rmtree(tmp_path)

def test_prepare_problem_files_template_copy(temp_dirs):
    manager = ContestFileManager(DummyFileOperator())
    manager.prepare_problem_files("abc100", "a", "python")
    # main.pyがコピーされているか
    assert Path("contest_current/python/main.py").exists()
    # info.jsonが正しく生成されているか
    info = json.loads(Path("contest_current/info.json").read_text())
    assert info["contest_name"] == "abc100"
    assert info["problem_name"] == "a"
    assert info["language_name"] == "python"

def test_prepare_problem_files_stocks_move(temp_dirs):
    # ストックにmain.pyを用意
    stocks = Path("contest_stocks/abc200/python")
    stocks.mkdir(parents=True)
    (stocks / "main.py").write_text("print('from stocks')\n")
    manager = ContestFileManager(DummyFileOperator())
    manager.prepare_problem_files("abc200", "b", "python")
    # main.pyがcontest_currentに移動されているか
    assert Path("contest_current/python/main.py").exists()
    # ストック側は空になっているか
    assert not stocks.exists() or not any(stocks.iterdir())
    # info.jsonが正しく生成されているか
    info = json.loads(Path("contest_current/info.json").read_text())
    assert info["contest_name"] == "abc200"
    assert info["problem_name"] == "b"
    assert info["language_name"] == "python"

def test_prepare_problem_files_not_found(temp_dirs):
    # contest_template/python ディレクトリを削除
    shutil.rmtree("contest_template/python")
    manager = ContestFileManager(DummyFileOperator())
    with pytest.raises(FileNotFoundError):
        manager.prepare_problem_files("abc999", "z", "python")

def test_move_current_to_stocks_basic(temp_dirs):
    # contest_current/python に main.py を用意
    current = Path("contest_current/python")
    current.mkdir(parents=True)
    (current / "main.py").write_text("print('move test')\n")
    # info.json, config.json を contest_current/ に用意
    info = {"contest_name": "abc300", "problem_name": "c", "language_name": "python"}
    Path("contest_current/info.json").write_text(json.dumps(info))
    Path("contest_current/config.json").write_text(json.dumps({"exclude_files": []}))
    manager = ContestFileManager(DummyFileOperator())
    manager.move_current_to_stocks("c", "python")
    # main.pyがcontest_stocksに移動されているか
    stocks = Path("contest_stocks/abc300/python/main.py")
    assert stocks.exists()
    # contest_current/python は削除されているか
    assert not current.exists()
    # info.json, config.json は contest_current/ に残るか
    assert Path("contest_current/info.json").exists()
    assert Path("contest_current/config.json").exists()

def test_copy_from_template_to_current_basic(temp_dirs):
    # contest_template/python に main.py を用意
    template = Path("contest_template/python")
    (template / "main.py").write_text("print('copy test')\n")
    manager = ContestFileManager(DummyFileOperator())
    manager.copy_from_template_to_current("abc400", "d", "python")
    # main.pyがcontest_currentにコピーされているか
    assert Path("contest_current/python/main.py").exists()
    # info.json, config.json が contest_current/ に生成されているか
    assert Path("contest_current/info.json").exists()
    assert Path("contest_current/config.json").exists()
    # info.jsonの内容確認
    info = json.loads(Path("contest_current/info.json").read_text())
    assert info["contest_name"] == "abc400"
    assert info["problem_name"] == "d"
    assert info["language_name"] == "python"

def test_problem_exists_in_stocks_and_current(temp_dirs):
    manager = ContestFileManager(DummyFileOperator())
    # stocksにmain.pyがある場合
    stocks = Path("contest_stocks/abc500/python")
    stocks.mkdir(parents=True)
    (stocks / "main.py").write_text("print('exists')\n")
    assert manager.problem_exists_in_stocks("abc500", "e", "python") is True
    # stocksが空の場合
    (stocks / "main.py").unlink()
    assert manager.problem_exists_in_stocks("abc500", "e", "python") is False
    # currentにmain.pyがある場合
    current = Path("contest_current/python")
    current.mkdir(parents=True)
    (current / "main.py").write_text("print('exists')\n")
    assert manager.problem_exists_in_current("abc500", "e", "python") is True
    # currentが空の場合
    (current / "main.py").unlink()
    assert manager.problem_exists_in_current("abc500", "e", "python") is False 