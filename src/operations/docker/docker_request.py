from enum import Enum, auto
from typing import Any, Dict, Optional
from src.operations.docker.docker_driver import DockerDriver, LocalDockerDriver
from src.operations.result import OperationResult
from src.operations.constants.operation_type import OperationType
import inspect
import os
from src.operations.base_request import BaseRequest
from src.operations.composite.composite_request import CompositeRequest

class DockerOpType(Enum):
    RUN = auto()
    STOP = auto()
    REMOVE = auto()
    EXEC = auto()
    LOGS = auto()
    INSPECT = auto()

class DockerRequest(BaseRequest):
    def __init__(self, op: DockerOpType, image: str = None, container: str = None, command: str = None, options: Optional[Dict[str, Any]] = None, debug_tag=None, name=None, show_output=True):
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op
        self.image = image
        self.container = container
        self.command = command
        self.options = options or {}
        self.show_output = show_output
        self._executed = False
        self._result = None

    @property
    def operation_type(self):
        return OperationType.DOCKER

    def execute(self, driver):
        return super().execute(driver)

    def _execute_core(self, driver):
        # 前処理が必要な場合はCompositeRequestとして分離
        if self.op == DockerOpType.RUN:
            if isinstance(driver, LocalDockerDriver) and self.container:
                # 0. psで存在確認
                container_names = driver.ps(all=True, show_output=False, names_only=True)
                if self.container not in container_names:
                    # 存在しなければrunのみ
                    return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)
                # 1. inspect
                inspect_result = driver.inspect(self.container, show_output=False)
                import json
                need_stop = False
                need_remove = False
                try:
                    inspect_data = json.loads(inspect_result.stdout)
                    if isinstance(inspect_data, list) and len(inspect_data) > 0:
                        state = inspect_data[0].get("State", {})
                        status = state.get("Status", "")
                        if status == "running":
                            need_stop = True
                            need_remove = True
                        elif status in ("exited", "created", "dead", "paused"):  # 停止中
                            need_remove = True
                except Exception:
                    pass
                reqs = []
                reqs.append(DockerRequest(DockerOpType.INSPECT, container=self.container, show_output=False))
                if need_stop:
                    reqs.append(DockerRequest(DockerOpType.STOP, container=self.container, show_output=False))
                if need_remove:
                    reqs.append(DockerRequest(DockerOpType.REMOVE, container=self.container, show_output=False))
                reqs.append(DockerRequest(DockerOpType.RUN, image=self.image, container=self.container, options=self.options, show_output=self.show_output))
                results = CompositeRequest.make_composite_request(reqs).execute(driver)
                if isinstance(results, list) and results:
                    return results[-1]  # 最後のOperationResult（=RUNの結果）を返す
                return results
        # 通常の単体リクエスト
        try:
            if self.op == DockerOpType.RUN:
                result = driver.run_container(self.image, self.container, self.options, show_output=self.show_output)
            elif self.op == DockerOpType.STOP:
                result = driver.stop_container(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.REMOVE:
                result = driver.remove_container(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.INSPECT:
                result = driver.inspect(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.EXEC:
                result = driver.exec_in_container(self.container, self.command, show_output=self.show_output)
            elif self.op == DockerOpType.LOGS:
                result = driver.get_logs(self.container, show_output=self.show_output)
            else:
                raise ValueError(f"Unknown DockerOpType: {self.op}")
            return OperationResult(
                op=self.op,
                stdout=getattr(result, 'stdout', None),
                stderr=getattr(result, 'stderr', None),
                returncode=getattr(result, 'returncode', None)
            )
        except Exception as e:
            return OperationResult(success=False, op=self.op, stdout=None, stderr=str(e), returncode=None)

    def __repr__(self):
        return f"<DockerRequest op={self.op} container={self.container} command={self.command}>" 