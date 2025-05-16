from enum import Enum, auto
from typing import Any, Dict, Optional
from src.operations.docker.docker_driver import DockerDriver, LocalDockerDriver

class DockerOpType(Enum):
    RUN = auto()
    STOP = auto()
    REMOVE = auto()
    EXEC = auto()
    LOGS = auto()

class DockerRequest:
    def __init__(self, op: DockerOpType, image: str = None, name: str = None, command: str = None, options: Optional[Dict[str, Any]] = None, driver: DockerDriver = None):
        self.op = op
        self.image = image
        self.name = name
        self.command = command
        self.options = options or {}
        self._driver = driver or LocalDockerDriver()
        self._executed = False
        self._result = None

    def execute(self):
        if self._executed:
            raise RuntimeError("This DockerRequest has already been executed.")
        try:
            if self.op == DockerOpType.RUN:
                result = self._driver.run_container(self.image, self.name, self.options)
            elif self.op == DockerOpType.STOP:
                result = self._driver.stop_container(self.name)
            elif self.op == DockerOpType.REMOVE:
                result = self._driver.remove_container(self.name)
            elif self.op == DockerOpType.EXEC:
                result = self._driver.exec_in_container(self.name, self.command)
            elif self.op == DockerOpType.LOGS:
                result = self._driver.get_logs(self.name)
            else:
                raise ValueError(f"Unknown DockerOpType: {self.op}")
            self._result = result
        except Exception as e:
            self._result = e
        self._executed = True
        return self._result 