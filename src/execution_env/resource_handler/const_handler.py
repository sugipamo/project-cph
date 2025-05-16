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



#↓仕様変更をするので、dictから読み込みするように変えたい↓

class LocalConstHandler(BaseConstHandler):

    def __init__(self, config: dict):
        super().__init__(config)

    @property
    def contest_current_path(self):
        return Path(self.base.contest_current_path)

    @property
    def source_file_path(self):
        return self.contest_current_path / self.base.source_file

    @property
    def env_type(self) -> EnvType:
        return EnvType.LOCAL

    @property
    def contest_env_path(self):
        return Path(self.base.contest_env_path)

    @property
    def contest_template_path(self):
        return Path(self.base.contest_template_path)

    @property
    def contest_temp_path(self):
        return Path(self.base.contest_temp_path)

    @property
    def test_case_path(self):
        return self.contest_current_path / "test"

    @property
    def test_case_in_path(self):
        return self.test_case_path / "in"

    @property
    def test_case_out_path(self):
        return self.test_case_path / "out"

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
        return self.contest_current_path / self.base.source_file

    @property
    def env_type(self) -> EnvType:
        return EnvType.DOCKER

    @property
    def contest_env_path(self):
        return self._to_container_path(self.base.contest_env_path)

    @property
    def contest_template_path(self):
        return self._to_container_path(self.base.contest_template_path)

    @property
    def contest_temp_path(self):
        return self._to_container_path(self.base.contest_temp_path)

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
        return f"{self.base.language}"