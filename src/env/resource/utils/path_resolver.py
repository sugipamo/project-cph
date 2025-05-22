from pathlib import Path
import os

class PathResolver:
    def __init__(self, config, workspace_path):
        self.config = config
        self._workspace_path = workspace_path

    @property
    def workspace_path(self) -> Path:
        if self._workspace_path is None:
            raise ValueError("workspace_pathがNoneです。必ず有効なパスを指定してください。")
        return Path(self._workspace_path)

    @property
    def contest_current_path(self) -> Path:
        if self.config.contest_current_path is None:
            raise ValueError("contest_current_pathがNoneです。必ず有効なパスを指定してください。")
        return Path(self.config.contest_current_path)

    @property
    def contest_env_path(self) -> Path:
        # まずenv_jsonにcontest_env_pathがあればそれを使う
        lang_conf = self.config.env_json[self.config.language]
        v = lang_conf.get("contest_env_path", None)
        if v is not None:
            return Path(v)
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
        try:
            v = self.config.env_json[self.config.language]["contest_template_path"]
        except KeyError:
            raise ValueError("contest_template_pathがNoneです。必ず有効なパスを指定してください。")
        return Path(v)

    @property
    def contest_temp_path(self) -> Path:
        try:
            v = self.config.env_json[self.config.language]["contest_temp_path"]
        except KeyError:
            raise ValueError("contest_temp_pathがNoneです。必ず有効なパスを指定してください。")
        return Path(v)

    @property
    def test_case_path(self) -> Path:
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self) -> Path:
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self) -> Path:
        return self.test_case_path / "out" 