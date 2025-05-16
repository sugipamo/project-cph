from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum, auto

class EnvType(Enum):
    LOCAL = auto()
    DOCKER = auto()

class BaseConstHandler(ABC):
    def __init__(self, config: dict, workspace: str = None):
        self.config = config
        self._workspace = workspace

    @property
    def workspace(self) -> Path:
        return Path(self._workspace)

    @property
    @abstractmethod
    def contest_current_path(self) -> Path: pass

    @property
    @abstractmethod
    def source_file_path(self) -> Path: pass

    @property
    @abstractmethod
    def env_type(self) -> EnvType: pass

    @abstractmethod
    def parse(self, s: str) -> str:
        pass

    @abstractmethod
    def parse_with_workspace(self, s: str) -> str:
        pass

    @property
    def workspace(self) -> Path:
        return Path(self._workspace)



class LocalConstHandler(BaseConstHandler):

    def __init__(self, config: dict, workspace: str = "/workspace"):
        super().__init__(config, workspace)
        self._workspace = workspace

    @property
    def contest_current_path(self) -> Path:
        return Path(self.config["contest_current_path"])

    @property
    def source_file_path(self) -> Path:
        return self.contest_current_path / self.config["source_file"]

    @property
    def env_type(self) -> EnvType:
        return EnvType.LOCAL

    @property
    def contest_env_path(self) -> Path:
        return Path(self.config["contest_env_path"])

    @property
    def contest_template_path(self) -> Path:
        return Path(self.config["contest_template_path"])

    @property
    def contest_temp_path(self) -> Path:
        return Path(self.config["contest_temp_path"])

    @property
    def test_case_path(self) -> Path:
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self) -> Path:
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self) -> Path:
        return self.test_case_path / "out"

    def parse(self, s: str) -> str:
        # 変数展開: {contest_current} など
        result = s
        result = result.replace("{contest_current}", str(self.contest_current_path))
        result = result.replace("{source_file}", str(self.source_file_path))
        result = result.replace("{contest_env}", str(self.contest_env_path))
        result = result.replace("{contest_template}", str(self.contest_template_path))
        result = result.replace("{contest_temp}", str(self.contest_temp_path))
        result = result.replace("{test_case}", str(self.test_case_path))
        result = result.replace("{test_case_in}", str(self.test_case_in_path))
        result = result.replace("{test_case_out}", str(self.test_case_out_path))
        return result

    def parse_with_workspace(self, s: str) -> str:
        # workspace/otherpath 形式でパースする
        if self.workspace:
            # すべてのパス変数をworkspace配下にする
            result = s
            result = result.replace("{contest_current}", str(Path(self.workspace) / Path(self.config["contest_current_path"])))
            result = result.replace("{source_file}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / self.config["source_file"])))
            result = result.replace("{contest_env}", str(Path(self.workspace) / Path(self.config["contest_env_path"])))
            result = result.replace("{contest_template}", str(Path(self.workspace) / Path(self.config["contest_template_path"])))
            result = result.replace("{contest_temp}", str(Path(self.workspace) / Path(self.config["contest_temp_path"])))
            result = result.replace("{test_case}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / "test")))
            result = result.replace("{test_case_in}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / "test" / "in")))
            result = result.replace("{test_case_out}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / "test" / "out")))
            return result
        else:
            return self.parse(s)

class DockerConstHandler(BaseConstHandler):
    def __init__(self, config: dict, workspace="/workspace"):
        super().__init__(config, workspace)
        self._workspace = workspace

    @property
    def contest_current_path(self) -> Path:
        return Path(self.config["contest_current_path"])

    @property
    def source_file_path(self) -> Path:
        return self.contest_current_path / self.config["source_file"]

    @property
    def env_type(self) -> EnvType:
        return EnvType.DOCKER

    @property
    def contest_env_path(self) -> Path:
        return Path(self.config["contest_env_path"])

    @property
    def contest_template_path(self) -> Path:
        return Path(self.config["contest_template_path"])

    @property
    def contest_temp_path(self) -> Path:
        return Path(self.config["contest_temp_path"])

    @property
    def test_case_path(self) -> Path:
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self) -> Path:
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self) -> Path:
        return self.test_case_path / "out"
    
    @property
    def image_name(self) -> str:
        return f"{self.config.get('language', '')}"

    def parse(self, s: str) -> str:
        # 変数展開: {contest_current} など（Docker用パスで）
        result = s
        result = result.replace("{contest_current}", str(self.contest_current_path))
        result = result.replace("{source_file}", str(self.source_file_path))
        result = result.replace("{contest_env}", str(self.contest_env_path))
        result = result.replace("{contest_template}", str(self.contest_template_path))
        result = result.replace("{contest_temp}", str(self.contest_temp_path))
        result = result.replace("{test_case}", str(self.test_case_path))
        result = result.replace("{test_case_in}", str(self.test_case_in_path))
        result = result.replace("{test_case_out}", str(self.test_case_out_path))
        return result
    
    def parse_with_workspace(self, s: str) -> str:
        # workspace/otherpath 形式でパースする
        if self.workspace:
            # すべてのパス変数をworkspace配下にする
            result = s
            result = result.replace("{contest_current}", str(Path(self.workspace) / Path(self.config["contest_current_path"])))
            result = result.replace("{source_file}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / self.config["source_file"])))
            result = result.replace("{contest_env}", str(Path(self.workspace) / Path(self.config["contest_env_path"])))
            result = result.replace("{contest_template}", str(Path(self.workspace) / Path(self.config["contest_template_path"])))
            result = result.replace("{contest_temp}", str(Path(self.workspace) / Path(self.config["contest_temp_path"])))
            result = result.replace("{test_case}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / "test")))
            result = result.replace("{test_case_in}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / "test" / "in")))
            result = result.replace("{test_case_out}", str(Path(self.workspace) / (Path(self.config["contest_current_path"]) / "test" / "out")))
            return result
        else:
            return self.parse(s)

