from pathlib import Path

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
        v = self.config.env_json.get("contest_env_path", "env")
        if v is None:
            raise ValueError("contest_env_pathがNoneです。必ず有効なパスを指定してください。")
        return Path(v)

    @property
    def contest_template_path(self) -> Path:
        v = self.config.env_json.get("contest_template_path", "template")
        if v is None:
            raise ValueError("contest_template_pathがNoneです。必ず有効なパスを指定してください。")
        return Path(v)

    @property
    def contest_temp_path(self) -> Path:
        v = self.config.env_json.get("contest_temp_path", "temp")
        if v is None:
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