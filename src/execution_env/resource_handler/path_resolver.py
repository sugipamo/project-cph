from pathlib import Path

class PathResolver:
    def __init__(self, config, workspace_path):
        self.config = config
        self._workspace_path = workspace_path

    @property
    def workspace_path(self) -> Path:
        return Path(self._workspace_path)

    @property
    def contest_current_path(self) -> Path:
        return Path(self.config.contest_current_path)

    @property
    def contest_env_path(self) -> Path:
        return Path(self.config.env_json.get("contest_env_path", "env"))

    @property
    def contest_template_path(self) -> Path:
        return Path(self.config.env_json.get("contest_template_path", "template"))

    @property
    def contest_temp_path(self) -> Path:
        return Path(self.config.env_json.get("contest_temp_path", "temp"))

    @property
    def test_case_path(self) -> Path:
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self) -> Path:
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self) -> Path:
        return self.test_case_path / "out" 