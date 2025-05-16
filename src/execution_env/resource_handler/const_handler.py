from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum, auto

class EnvType(Enum):
    LOCAL = auto()
    DOCKER = auto()

class BaseConstHandler(ABC):
    def __init__(self, config: dict):
        self.config = config

    @property
    @abstractmethod
    def contest_current_path(self): pass

    @property
    @abstractmethod
    def source_file_path(self): pass

    @property
    @abstractmethod
    def env_type(self) -> EnvType: pass

    @abstractmethod
    def parse(self, s: str) -> str:
        pass



#↓仕様変更をするので、dictから読み込みするように変えたい↓

class LocalConstHandler(BaseConstHandler):

    def __init__(self, config: dict):
        super().__init__(config)

    @property
    def contest_current_path(self):
        return Path(self.config["contest_current_path"])

    @property
    def source_file_path(self):
        return self.contest_current_path / self.config["source_file"]

    @property
    def env_type(self) -> EnvType:
        return EnvType.LOCAL

    @property
    def contest_env_path(self):
        return Path(self.config["contest_env_path"])

    @property
    def contest_template_path(self):
        return Path(self.config["contest_template_path"])

    @property
    def contest_temp_path(self):
        return Path(self.config["contest_temp_path"])

    @property
    def test_case_path(self):
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self):
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self):
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

class DockerConstHandler(BaseConstHandler):
    def __init__(self, config: dict, container_workspace="/workspace"):
        super().__init__(config)
        self.container_workspace = container_workspace

    def _to_container_path(self, path):
        path = Path(path).resolve()
        root = Path(".").resolve()
        rel_path = path.relative_to(root)
        return Path(self.container_workspace) / rel_path

    @property
    def contest_current_path(self):
        return self._to_container_path(self.config["contest_current_path"])

    @property
    def source_file_path(self):
        return self.contest_current_path / self.config["source_file"]

    @property
    def env_type(self) -> EnvType:
        return EnvType.DOCKER

    @property
    def contest_env_path(self):
        return self._to_container_path(self.config["contest_env_path"])

    @property
    def contest_template_path(self):
        return self._to_container_path(self.config["contest_template_path"])

    @property
    def contest_temp_path(self):
        return self._to_container_path(self.config["contest_temp_path"])

    @property
    def test_case_path(self):
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self):
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self):
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