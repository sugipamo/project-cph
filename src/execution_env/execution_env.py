import importlib
import pkgutil
from pathlib import Path
from abc import ABC, abstractmethod
from enum import Enum, auto
from execution_client.client.local import LocalAsyncClient
from execution_client.client.container import ContainerClient

BASE_DIR = "contest_env"

class ExecutionEnvType(Enum):
    LOCAL = auto()
    DOCKER = auto()

class ExecutionStatus(Enum):
    INIT = auto()
    BUILT = auto()
    READY = auto()
    RUNNING = auto()
    FINISHED = auto()
    ERROR = auto()

class BaseExecutionEnv(ABC):
    def __init__(self, base_handler):
        self.base = base_handler
        self.status = ExecutionStatus.INIT

    @property
    @abstractmethod
    def contest_current_path(self): pass

    @property
    @abstractmethod
    def source_file_path(self): pass

    @property
    @abstractmethod
    def env_type(self) -> ExecutionEnvType: pass

    def set_status(self, status: ExecutionStatus):
        self.status = status

    def get_status(self) -> ExecutionStatus:
        return self.status

class LocalExecutionEnv(BaseExecutionEnv):
    execution_client_class = LocalAsyncClient

    @property
    def contest_current_path(self):
        return Path(self.base.contest_current_path)

    @property
    def source_file_path(self):
        return self.contest_current_path / self.base.source_file

    @property
    def env_type(self) -> ExecutionEnvType:
        return ExecutionEnvType.LOCAL

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

class DockerExecutionEnv(BaseExecutionEnv):
    execution_client_class = ContainerClient

    def __init__(self, base_handler, container_workspace="/workspace"):
        super().__init__(base_handler)
        self.container_workspace = container_workspace

    def _to_container_path(self, path):
        path = Path(path).resolve()
        root = Path(".").resolve()
        rel_path = path.relative_to(root)
        return Path(self.container_workspace) / rel_path

    @property
    def contest_current_path(self):
        return self._to_container_path(self.base.contest_current_path)

    @property
    def source_file_path(self):
        return self.contest_current_path / self.base.source_file

    @property
    def env_type(self) -> ExecutionEnvType:
        return ExecutionEnvType.DOCKER

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

# ファクトリパターン（predicate関数による自動判別型）
class ExecutionEnvFactory:
    _registry = []

    @classmethod
    def register(cls, predicate):
        def decorator(env_cls):
            cls._registry.append((predicate, env_cls))
            return env_cls
        return decorator

    @classmethod
    def create(cls, base_handler, **kwargs) -> BaseExecutionEnv:
        for predicate, env_cls in cls._registry:
            if predicate(base_handler):
                return env_cls(base_handler, **kwargs)
        raise ValueError("No suitable ExecutionEnv found")
