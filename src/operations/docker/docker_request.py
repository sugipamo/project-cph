from enum import Enum, auto
from typing import Any, Dict, Optional
from src.operations.docker.docker_driver import DockerDriver, LocalDockerDriver
from src.operations.result import OperationResult
from src.operations.operation_type import OperationType
import inspect
import os
from src.operations.request_debug_info_mixin import RequestDebugInfoMixin

class DockerOpType(Enum):
    RUN = auto()
    STOP = auto()
    REMOVE = auto()
    EXEC = auto()
    LOGS = auto()

class DockerRequest(RequestDebugInfoMixin):
    def __init__(self, op: DockerOpType, image: str = None, name: str = None, command: str = None, options: Optional[Dict[str, Any]] = None, debug_tag=None):
        self.op = op
        self.image = image
        self.name = name
        self.command = command
        self.options = options or {}
        self._executed = False
        self._result = None
        self._set_debug_info(debug_tag)

    @property
    def operation_type(self):
        return OperationType.DOCKER

    def execute(self, driver=None):
        if self._executed:
            raise RuntimeError("This DockerRequest has already been executed.")
        if driver is None:
            raise ValueError("DockerRequest.execute()にはdriverが必須です")
        try:
            if self.op == DockerOpType.RUN:
                result = driver.run_container(self.image, self.name, self.options)
            elif self.op == DockerOpType.STOP:
                result = driver.stop_container(self.name)
            elif self.op == DockerOpType.REMOVE:
                result = driver.remove_container(self.name)
            elif self.op == DockerOpType.EXEC:
                result = driver.exec_in_container(self.name, self.command)
            elif self.op == DockerOpType.LOGS:
                result = driver.get_logs(self.name)
            else:
                raise ValueError(f"Unknown DockerOpType: {self.op}")
            self._result = OperationResult(success=True, op=self.op, stdout=result.stdout if hasattr(result, 'stdout') else None, stderr=result.stderr if hasattr(result, 'stderr') else None, returncode=result.returncode if hasattr(result, 'returncode') else None)
        except Exception as e:
            self._result = OperationResult(success=False, op=self.op, stdout=None, stderr=str(e), returncode=None)
        self._executed = True
        return self._result

    def __repr__(self):
        return f"<DockerRequest op={self.op} name={self.name} command={self.command}>" 