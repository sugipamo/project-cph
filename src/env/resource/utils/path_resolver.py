from pathlib import Path
import os

class PathResolver:
    def __init__(self, config):
        self.config = config

    @property
    def workspace_path(self) -> Path:
        return Path(self.config.resolver.resolve_best([self.config.language, "workspace_path"]).value)

    @property
    def contest_current_path(self) -> Path:
        return Path(self.config.resolver.resolve_best([self.config.language, "contest_current_path"]).value)

    @property
    def contest_env_path(self) -> Path:
        # 無ければ親ディレクトリをたどってcontest_envを探す
        cur = os.path.abspath(os.getcwd())
        while True:
            candidate = os.path.join(cur, "contest_env")
            if os.path.isdir(candidate):
                return Path(candidate)
            parent = os.path.dirname(cur)
            if parent == cur:
                break
            cur = parent
        raise ValueError("contest_env_pathが自動検出できませんでした。contest_envディレクトリが見つかりません。")

    @property
    def contest_template_path(self) -> Path:
        return Path(self.config.resolver.resolve_best([self.config.language, "contest_template_path"]).value)

    @property
    def contest_temp_path(self) -> Path:
        return Path(self.config.resolver.resolve_best([self.config.language, "contest_temp_path"]).value)

    @property
    def test_case_path(self) -> Path:
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self) -> Path:
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self) -> Path:
        return self.test_case_path / "out" 