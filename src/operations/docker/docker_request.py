from enum import Enum, auto
from typing import Any, Dict, Optional
from src.operations.docker.docker_driver import DockerDriver, LocalDockerDriver
from src.operations.result import OperationResult
from src.operations.operation_type import OperationType
import inspect
import os
from src.operations.base_request import BaseRequest

class DockerOpType(Enum):
    RUN = auto()
    STOP = auto()
    REMOVE = auto()
    EXEC = auto()
    LOGS = auto()

class DockerRequest(BaseRequest):
    def __init__(self, op: DockerOpType, image: str = None, container: str = None, command: str = None, options: Optional[Dict[str, Any]] = None, debug_tag=None, name=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op
        self.image = image
        self.container = container
        self.command = command
        self.options = options or {}
        self._executed = False
        self._result = None

    @property
    def operation_type(self):
        return OperationType.DOCKER

    def execute(self, driver):
        if self._executed:
            raise RuntimeError("This DockerRequest has already been executed.")
        if driver is None:
            raise ValueError("DockerRequest.execute()にはdriverが必須です")
        try:
            if self.op == DockerOpType.RUN:
                result = driver.run_container(self.image, self.container, self.options)
            elif self.op == DockerOpType.STOP:
                result = driver.stop_container(self.container)
            elif self.op == DockerOpType.REMOVE:
                result = driver.remove_container(self.container)
            elif self.op == DockerOpType.EXEC:
                result = driver.exec_in_container(self.container, self.command)
            elif self.op == DockerOpType.LOGS:
                result = driver.get_logs(self.container)
            else:
                raise ValueError(f"Unknown DockerOpType: {self.op}")
            self._result = OperationResult(
                op=self.op,
                stdout=getattr(result, 'stdout', None),
                stderr=getattr(result, 'stderr', None),
                returncode=getattr(result, 'returncode', None)
            )
        except Exception as e:
            self._result = OperationResult(success=False, op=self.op, stdout=None, stderr=str(e), returncode=None)
        self._executed = True
        return self._result

    def __repr__(self):
        return f"<DockerRequest op={self.op} container={self.container} command={self.command}>" 