from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum, auto
import hashlib
from src.operations.file.file_driver import LocalFileDriver
from src.execution_context.execution_context import ExecutionContext

class EnvType(Enum):
    LOCAL = auto()
    DOCKER = auto()

class BaseConstHandler(ABC):
    def __init__(self, config: ExecutionContext, workspace_path: str = None):
        self.config = config
        self._workspace_path = workspace_path

    @property
    def workspace_path(self) -> Path:
        return Path(self._workspace_path)
    
    @property
    def contest_current_path(self) -> Path:
        return Path(self.config.contest_current_path)

    @property
    def source_file_name(self) -> str:
        return self.config.env_json.get("source_file_name", "main.cpp")

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
    
    def parse(self, s: str) -> str:
        # 変数展開: {contest_current} など
        result = s
        result = result.replace("{workspace_path}", str(self.workspace_path))
        result = result.replace("{contest_current_path}", str(self.contest_current_path))
        result = result.replace("{source_file}", str(self.source_file_name))
        result = result.replace("{source_file_name}", str(self.source_file_name))
        result = result.replace("{contest_env}", str(self.contest_env_path))
        result = result.replace("{contest_template}", str(self.contest_template_path))
        result = result.replace("{contest_temp}", str(self.contest_temp_path))
        result = result.replace("{test_case}", str(self.test_case_path))
        result = result.replace("{test_case_in}", str(self.test_case_in_path))
        result = result.replace("{test_case_out}", str(self.test_case_out_path))
        return result


class LocalConstHandler(BaseConstHandler):

    def __init__(self, config: ExecutionContext, workspace_path: str = "./workspace_path"):
        super().__init__(config, workspace_path)
        self._workspace = workspace_path

    @property
    def env_type(self) -> EnvType:
        return EnvType.LOCAL


class DockerConstHandler(BaseConstHandler):
    def __init__(self, config: ExecutionContext, workspace_path="./workspace_path"):
        super().__init__(config, workspace_path)
        self._workspace = workspace_path

    @property
    def env_type(self) -> EnvType:
        return EnvType.DOCKER
    
    @property
    def image_name(self) -> str:
        # Dockerfileの内容をハッシュ化し、languagename_hash形式で返す
        language = self.config.language
        dockerfile_path = self.config.env_json.get("dockerfile_path")
        if not dockerfile_path:
            return language
        file_driver = LocalFileDriver()
        hash_str = file_driver.hash_file(dockerfile_path)
        return f"{language}_{hash_str}"

    @property
    def container_name(self) -> str:
        return f"cph_{self.image_name}"

    @property
    def base_image_name(self) -> str:
        # ハッシュを除いたベースのイメージ名（例: "python" など）
        return self.config.language

    @property
    def oj_dockerfile_path(self) -> str:
        return Path("./src/execution_env/oj/Dockerfile")

    @property
    def base_oj_image_name(self) -> str:
        return "cph_ojtools"

    @property
    def oj_image_name(self) -> str:
        file_driver = LocalFileDriver()
        hash_str = file_driver.hash_file(self.oj_dockerfile_path)
        return f"{self.base_oj_image_name}_{hash_str}"


    @property
    def oj_container_name(self) -> str:
        # env_jsonにoj_container_nameがあればそれを、なければデフォルト値
        return self.config.env_json.get("cph_ojtools")
