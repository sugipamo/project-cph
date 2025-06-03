from enum import Enum, auto
from typing import Any, Dict, Optional, Union, List
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
    BUILD = auto()
    CP = auto()

class DockerRequest(BaseRequest):
    def __init__(self, op: DockerOpType, image: str = None, container: str = None, command: Union[str, List[str]] = None, options: Optional[Dict[str, Any]] = None, debug_tag=None, name=None, show_output=True, dockerfile_text=None):
        super().__init__(name=name, debug_tag=debug_tag)
        self.op = op
        self.image = image
        self.container = container
        self.command = command
        self.options = options or {}
        self.show_output = show_output
        self._executed = False
        self._result = None
        self.dockerfile_text = dockerfile_text

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
                try:
                    inspect_data = json.loads(inspect_result.stdout)
                    if isinstance(inspect_data, list) and len(inspect_data) > 0:
                        state = inspect_data[0].get("State", {})
                        status = state.get("Status", "")
                        reqs = []
                        if status == "running":
                            # 既に起動中なら何もしない（再利用）
                            return OperationResult(success=True, op=self.op, stdout="already running", stderr=None, returncode=0)
                        elif status in ("exited", "created", "dead", "paused"):
                            # 停止中ならrm
                            reqs.append(DockerRequest(DockerOpType.REMOVE, container=self.container, show_output=False))
                        # いずれの場合もrun
                        reqs.append(DockerRequest(DockerOpType.RUN, image=self.image, container=self.container, options=self.options, show_output=self.show_output))
                        results = CompositeRequest.make_composite_request(reqs).execute(driver)
                        if isinstance(results, list) and results:
                            return results[-1]
                        return results
                except Exception:
                    # inspect失敗時はrunのみ
                    return driver.run_container(self.image, self.container, self.options, show_output=self.show_output)
        # 通常の単体リクエスト
        try:
            if self.op == DockerOpType.RUN:
                result = driver.run_container(self.image, self.container, self.options, show_output=self.show_output)
            elif self.op == DockerOpType.STOP:
                result = driver.stop_container(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.REMOVE:
                force = self.options.get('f') is not None if self.options else False
                result = driver.remove_container(self.container, force=force, show_output=self.show_output)
            elif self.op == DockerOpType.INSPECT:
                result = driver.inspect(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.EXEC:
                result = driver.exec_in_container(self.container, self.command, show_output=self.show_output)
            elif self.op == DockerOpType.LOGS:
                result = driver.get_logs(self.container, show_output=self.show_output)
            elif self.op == DockerOpType.BUILD:
                # BUILD用の処理
                tag = self.options.get('t')
                result = driver.build(self.dockerfile_text, tag=tag, options=self.options, show_output=self.show_output)
            elif self.op == DockerOpType.CP:
                # CP用の処理
                local_path = self.options.get('local_path')
                remote_path = self.options.get('remote_path')
                to_container = self.options.get('to_container', True)
                if to_container:
                    result = driver.cp(local_path, remote_path, self.container, to_container=True, show_output=self.show_output)
                else:
                    result = driver.cp(remote_path, local_path, self.container, to_container=False, show_output=self.show_output)
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