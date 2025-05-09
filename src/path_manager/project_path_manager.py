import os
from pathlib import Path
from typing import Optional

class ProjectPathManager:
    """
    contest_current, contest_stocks, contest_env, contest_template などの
    プロジェクト内パスを一元管理するクラス。
    """
    def __init__(self, root: Optional[str] = None):
        self.root = Path(root).resolve() if root else Path.cwd().resolve()

    # contest_current
    def contest_current(self, *paths) -> Path:
        return self.root / "contest_current" / Path(*paths) if paths else self.root / "contest_current"

    # contest_stocks
    def contest_stocks(self, contest_name: Optional[str] = None, problem_name: Optional[str] = None, language_name: Optional[str] = None, *paths) -> Path:
        parts = ["contest_stocks"]
        if contest_name:
            parts.append(contest_name)
        if problem_name:
            parts.append(problem_name)
        if language_name:
            parts.append(language_name)
        p = self.root
        for part in parts:
            p = p / part
        if paths:
            p = p / Path(*paths)
        return p

    # contest_env
    def contest_env(self, filename: str) -> Path:
        return self.root / "contest_env" / filename

    # contest_template
    def contest_template(self, language_name: Optional[str] = None, *paths) -> Path:
        p = self.root / "contest_template"
        if language_name:
            p = p / language_name
        if paths:
            p = p / Path(*paths)
        return p

    # 例: system_info.json, config.json, testディレクトリなどのショートカット
    def info_json(self) -> Path:
        return self.contest_current("system_info.json")

    def config_json(self) -> Path:
        return self.contest_current("config.json")

    def test_dir(self) -> Path:
        return self.contest_current("test")

    def readme_md(self) -> Path:
        return self.contest_current("README.md") 