import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent.parent / "src"))
import shutil
from pathlib import Path as PPath
import pytest
from file_operator import LocalFileOperator

tmp_dir = PPath("tests/file_operator/tmp")

def setup_function():
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)
    tmp_dir.mkdir(parents=True, exist_ok=True)

def teardown_function():
    if tmp_dir.exists():
        shutil.rmtree(tmp_dir)

def test_create_file():
    op = LocalFileOperator()
    file_path = tmp_dir / "sample.txt"
    content = "Hello, world!"
    op.create(file_path, content)
    assert file_path.exists()
    with open(file_path, encoding="utf-8") as f:
        assert f.read() == content

def test_create_file_in_subdir():
    op = LocalFileOperator()
    file_path = tmp_dir / "subdir" / "sample2.txt"
    content = "Subdir test"
    op.create(file_path, content)
    assert file_path.exists()
    with open(file_path, encoding="utf-8") as f:
        assert f.read() == content 