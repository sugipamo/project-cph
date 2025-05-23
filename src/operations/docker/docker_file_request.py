from src.operations.result import OperationResult
import time
import inspect
import os
from src.operations.base_request import BaseRequest

class DockerFileRequest(BaseRequest):
    def __init__(self, src_path, dst_path, container, to_container=None, debug_tag=None):
        super().__init__(debug_tag=debug_tag)
        self.src_path = src_path
        self.dst_path = dst_path
        self.container = container
        self.to_container = to_container
        self._executed = False
        self._result = None

    def execute(self, driver):
        return super().execute(driver)

    def _execute_core(self, driver):
        if self.to_container is None:
            raise ValueError("to_containerが必要です")
        start_time = time.time()
        try:
            driver.cp(self.src_path, self.dst_path, self.container, to_container=self.to_container)
            return OperationResult(success=True, path=self.src_path, op="DOCKER_CP", request=self, start_time=start_time, end_time=time.time())
        except Exception as e:
            raise RuntimeError(f"DockerFileRequest failed: {str(e)}")

    def __repr__(self):
        return f"<DockerFileRequest src={self.src_path} dst={self.dst_path} container={self.container} to_container={self.to_container}>"

    @property
    def operation_type(self):
        from src.operations.constants.operation_type import OperationType
        return OperationType.DOCKER 