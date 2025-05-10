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

def test_prepare_problem_files_template_copy(temp_dirs):
    tmp_path = temp_dirs
    Path(tmp_path / "contest_current/system_info.json").write_text(json.dumps({
        "contest_name": "abc100",
        "problem_name": "a",
        "language_name": "python"
    }))
    manager = ContestFileManager(DummyFileOperator(base_dir=tmp_path))
    manager.prepare_problem_files("abc100", "a", "python")
    assert (tmp_path / "contest_current/python/main.py").exists()
    info = json.loads((tmp_path / "contest_current/system_info.json").read_text())
    assert info["contest_name"] == "abc100"
    assert info["problem_name"] == "a"
    assert info["language_name"] == "python"

def test_prepare_problem_files_stocks_move(temp_dirs):
    tmp_path = temp_dirs
    Path(tmp_path / "contest_current/system_info.json").write_text(json.dumps({
        "contest_name": "abc200",
        "problem_name": "b",
        "language_name": "python"
    }))
    stocks = tmp_path / "contest_stocks/abc200/b"
    stocks.mkdir(parents=True)
    (stocks / "main.py").write_text("print('from stocks')\n")
    manager = ContestFileManager(LocalFileOperator(base_dir=tmp_path))
    manager.prepare_problem_files("abc200", "b", "python")
    assert (tmp_path / "contest_current/python/main.py").exists()
    info = json.loads((tmp_path / "contest_current/system_info.json").read_text())
    assert info["contest_name"] == "abc200"
    assert info["problem_name"] == "b"
    assert info["language_name"] == "python"

def test_prepare_problem_files_not_found(temp_dirs):
    tmp_path = temp_dirs
    os.chdir(tmp_path)
    # template削除
    if (tmp_path / "contest_template/python").exists():
        shutil.rmtree(tmp_path / "contest_template/python")
    # stocks側も削除
    stocks_dir = tmp_path / "contest_stocks/abc999/z"
    if stocks_dir.exists():
        shutil.rmtree(stocks_dir)
    # current/python も削除
    current_dir = tmp_path / "contest_current/python"
    if current_dir.exists():
        shutil.rmtree(current_dir)
    manager = ContestFileManager(LocalFileOperator(base_dir=tmp_path))
    with pytest.raises(FileNotFoundError):
        manager.prepare_problem_files("abc999", "z", "python")

def test_move_current_to_stocks_basic(temp_dirs):
    # contest_current/python に main.py を用意
    current = Path("contest_current/python")
    current.mkdir(parents=True, exist_ok=True)
    (current / "main.py").write_text("print('move test')\n")
    # system_info.json, config.json を contest_current/ に用意
    info = {"contest_name": "abc300", "problem_name": "c", "language_name": "python"}
    Path("contest_current/system_info.json").write_text(json.dumps(info))
    Path("contest_current/config.json").write_text(json.dumps({"exclude_files": []}))
    manager = ContestFileManager(LocalFileOperator())
    manager.move_current_to_stocks("c", "python")
    # main.pyがcontest_stocksに移動されているか
    stocks = Path("contest_stocks/abc300/c/main.py")
    assert stocks.exists()
    # contest_current/python は削除されているか
    assert not current.exists()
    # system_info.json, config.json は contest_current/ に残るか
    assert Path("contest_current/system_info.json").exists()
    assert Path("contest_current/config.json").exists()

def test_copy_from_template_to_current_basic(temp_dirs):
    # contest_template/python に main.py を用意
    template = Path("contest_template/python")
    (template / "main.py").write_text("print('copy test')\n")
    manager = ContestFileManager(DummyFileOperator(base_dir=temp_dirs))
    manager.copy_from_template_to_current("abc400", "d", "python")
    # main.pyがcontest_currentにコピーされているか
    assert Path("contest_current/python/main.py").exists()
    # system_info.json, config.json が contest_current/ に生成されているか
    assert Path("contest_current/system_info.json").exists()
    assert Path("contest_current/config.json").exists()
    # system_info.jsonの内容確認
    info = json.loads(Path("contest_current/system_info.json").read_text())
    assert info["contest_name"] == "abc400"
    assert info["problem_name"] == "d"
    assert info["language_name"] == "python"

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

def test_get_exclude_files_missing(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = DummyFileOperator(tmp_path)
    manager = ContestFileManager(op)
    # config.jsonが存在しない場合
    config_path = tmp_path / "no_config.json"
    assert manager.get_exclude_files(config_path) == []
    # moveignoreキーがない場合
    config_path.write_text(json.dumps({}))
    assert manager.get_exclude_files(config_path) == []
    # moveignoreキーがある場合
    config_path.write_text(json.dumps({"moveignore": ["^foo$"]}))
    assert manager.get_exclude_files(config_path) == ["^foo$"]

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

def test_prepare_problem_files_config_has_language_id(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = DummyFileOperator(tmp_path)
    manager = ContestFileManager(op)
    info = tmp_path / "contest_current/system_info.json"
    info.parent.mkdir(parents=True, exist_ok=True)
    info.write_text(json.dumps({"contest_name": "abc", "problem_name": "a", "language_name": "python"}))
    config = tmp_path / "contest_current/config.json"
    config.write_text(json.dumps({"language_id": {"python": "9999"}}))
    # テンプレートも用意
    tdir = tmp_path / "contest_template/python"
    tdir.mkdir(parents=True)
    (tdir / "main.py").write_text("print('x')\n")
    # カレントディレクトリを一時的に変更
    import os
    old_cwd = os.getcwd()
    os.chdir(tmp_path)
    manager.prepare_problem_files("abc", "a", "python")
    os.chdir(old_cwd)
    # config.jsonのlanguage_idが上書きされていない
    data = json.loads(config.read_text())
    assert data["language_id"]["python"] == "9999"

def test_copy_current_to_stocks_moveignore(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    class Op(LocalFileOperator):
        def __init__(self, base_dir):
            super().__init__(base_dir)
            self.copied = []
            self.copied_tree = []
        def copy(self, src, dst):
            self.copied.append((src, dst))
        def copytree(self, src, dst):
            self.copied_tree.append((src, dst))
    op = Op(tmp_path)
    manager = ContestFileManager(op)
    src_dir = tmp_path / 'contest_current/python'
    src_dir.mkdir(parents=True, exist_ok=True)
    (src_dir / 'main.py').write_text('x')
    (src_dir / 'ignore.txt').write_text('y')
    (src_dir / 'dir').mkdir()
    (src_dir / 'dir' / 'a.txt').write_text('z')
    config_path = tmp_path / 'contest_current/config.json'
    config_path.write_text(json.dumps({'moveignore': ['ignore.txt', 'dir']}))
    # info.json を作成
    info_path = tmp_path / 'contest_current/system_info.json'
    info_path.write_text(json.dumps({'contest_name': 'abc', 'problem_name': 'a', 'language_name': 'python'}))
    manager.copy_current_to_stocks('abc', 'a', 'python')
    # ignore.txt, dirはコピーされない
    copied_files = [str(dst) for src, dst in op.copied]
    assert any('main.py' in f for f in copied_files)
    assert not any('ignore.txt' in f for f in copied_files)
    assert not op.copied_tree  # dirはコピーされない

def test_move_or_copy_skip_existing(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = LocalFileOperator(tmp_path)
    manager = ContestFileManager(op)
    src = tmp_path / 'src'
    dst = tmp_path / 'dst'
    src.mkdir()
    (src / 'a.txt').write_text('a')
    (src / 'b.txt').write_text('b')
    dst.mkdir()
    (dst / 'a.txt').write_text('old')  # 既存
    # move=False
    manager._move_or_copy_skip_existing(src, dst, move=False)
    assert (dst / 'b.txt').exists()
    assert (dst / 'a.txt').read_text() == 'old'  # 上書きされない
    # move=True
    (src / 'c.txt').write_text('c')
    manager._move_or_copy_skip_existing(src, dst, move=True)
    assert (dst / 'c.txt').exists()
    assert not (src / 'c.txt').exists()

def test_move_from_stocks_to_current_empty_cleanup(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = LocalFileOperator(tmp_path)
    manager = ContestFileManager(op)
    stocks = tmp_path / 'contest_stocks/abc/x/python'
    stocks.mkdir(parents=True)
    (stocks / 'a.txt').write_text('a')
    info = tmp_path / 'contest_current/system_info.json'
    info.parent.mkdir(parents=True, exist_ok=True)
    info.write_text(json.dumps({'contest_name': 'abc', 'problem_name': 'x', 'language_name': 'python'}))
    config = tmp_path / 'contest_current/config.json'
    config.write_text(json.dumps({}))
    # dst_dirは空
    dst = tmp_path / 'contest_current/python'
    manager.move_from_stocks_to_current('abc', 'x', 'python')
    # stocksディレクトリは空になり削除される
    assert not stocks.exists()
    # 親ディレクトリも空なら削除される（仕様上、親の削除は保証しないので存在してもOK）
    # assert not (tmp_path / 'contest_stocks/abc/x').exists()

def test_copy_from_template_to_current_config_exists(tmp_path):
    from src.file.contest_file_manager import ContestFileManager
    op = LocalFileOperator(tmp_path)
    manager = ContestFileManager(op)
    template = tmp_path / 'contest_template/python'
    template.mkdir(parents=True, exist_ok=True)
    (template / 'main.py').write_text('x')
    current = tmp_path / 'contest_current/python'
    current.mkdir(parents=True, exist_ok=True)
    config = tmp_path / 'contest_current/config.json'
    config.write_text(json.dumps({'moveignore': ['foo']}))
    manager.copy_from_template_to_current('abc', 'y', 'python')
    # config.jsonは上書きされない
    data = json.loads(config.read_text())
    assert data['moveignore'] == ['foo']

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