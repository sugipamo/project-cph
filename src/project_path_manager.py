import os
from typing import Optional

class ProjectPathManager:
    """
    contest_current, contest_stocks, contest_env, contest_template などの
    プロジェクト内パスを一元管理するクラス。
    """
    def __init__(self, root: Optional[str] = None):
        self.root = os.path.abspath(root) if root else os.path.abspath(".")

    # contest_current
    def contest_current(self, *paths) -> str:
        return os.path.join(self.root, "contest_current", *paths)

    # contest_stocks
    def contest_stocks(self, contest_name: Optional[str] = None, problem_name: Optional[str] = None, language_name: Optional[str] = None, *paths) -> str:
        parts = ["contest_stocks"]
        if contest_name:
            parts.append(contest_name)
        if problem_name:
            parts.append(problem_name)
        if language_name:
            parts.append(language_name)
        if paths:
            parts.extend(paths)
        return os.path.join(self.root, *parts)

    # contest_env
    def contest_env(self, filename: str) -> str:
        return os.path.join(self.root, "contest_env", filename)

    # contest_template
    def contest_template(self, language_name: Optional[str] = None, *paths) -> str:
        parts = ["contest_template"]
        if language_name:
            parts.append(language_name)
        if paths:
            parts.extend(paths)
        return os.path.join(self.root, *parts)

    # 例: info.json, config.json, testディレクトリなどのショートカット
    def info_json(self) -> str:
        return self.contest_current("info.json")

    def config_json(self) -> str:
        return self.contest_current("config.json")

    def test_dir(self) -> str:
        return self.contest_current("test")

    def readme_md(self) -> str:
        return self.contest_current("README.md") 