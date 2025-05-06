import pytest
from src.command_executor import MockOpener
import shutil
import os
import pathlib
import json

@pytest.fixture(autouse=True)
def patch_opener(monkeypatch):
    monkeypatch.setattr("src.command_executor.Opener", MockOpener)

@pytest.fixture(autouse=True)
def prepare_contest_current(tmp_path, monkeypatch):
    """
    contest_currentディレクトリと必要なファイル・ディレクトリを一時ディレクトリに新規生成し、
    カレントディレクトリを一時ディレクトリに切り替えるfixture。
    """
    dst_dir = tmp_path / "contest_current"
    dst_dir.mkdir(parents=True, exist_ok=True)
    # python/main.py
    py_dir = dst_dir / "python"
    py_dir.mkdir(exist_ok=True)
    main_py = py_dir / "main.py"
    if not main_py.exists():
        main_py.write_text(
            """# a.py\n# 問題: a\n# 言語: python\n\nif __name__ == \"__main__\":\n    pass\n""",
            encoding="utf-8"
        )
    # testケース
    test_dir = dst_dir / "test"
    test_dir.mkdir(exist_ok=True)
    # サンプルテストケース
    samples = [
        ("sample-1.in", "3 125 175\n200 300 400\n"),
        ("sample-1.out", "2\n"),
        ("sample-2.in", "1 1 1\n2\n"),
        ("sample-2.out", "1\n"),
        ("sample-3.in", "5 123 456\n135 246 357 468 579\n"),
        ("sample-3.out", "5\n"),
    ]
    for fname, content in samples:
        fpath = test_dir / fname
        if not fpath.exists():
            fpath.write_text(content, encoding="utf-8")
    # info.json
    info_json = dst_dir / "info.json"
    if not info_json.exists():
        info_json.write_text(json.dumps({
            "contest_name": "abc300",
            "problem_name": "a",
            "language_name": "python",
            "containers": [
                {"name": "test1", "type": "test"}
            ]
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    # config.json
    config_json = dst_dir / "config.json"
    if not config_json.exists():
        config_json.write_text(json.dumps({
            "language_id": {
                "python": "5082",
                "pypy": "5078",
                "rust": "5054"
            }
        }, ensure_ascii=False, indent=2), encoding="utf-8")
    # カレントディレクトリをtmp_pathに切り替え
    monkeypatch.chdir(tmp_path) 