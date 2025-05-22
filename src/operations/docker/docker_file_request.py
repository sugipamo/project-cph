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
        if self._executed:
            raise RuntimeError("This DockerFileRequest has already been executed.")
        if driver is None:
            raise ValueError("DockerFileRequest.execute()にはdriverが必須です")
        if self.to_container is None:
            raise ValueError("to_containerが必要です")
        start_time = time.time()
        try:
            driver.cp(self.src_path, self.dst_path, self.container, to_container=self.to_container)
            self._result = OperationResult(success=True, path=self.src_path, op="DOCKER_CP", request=self, start_time=start_time, end_time=time.time())
        except Exception as e:
            self._result = OperationResult(success=False, path=self.src_path, op="DOCKER_CP", request=self, start_time=start_time, end_time=time.time(), error_message=str(e), exception=e)
            self._executed = True
            raise
        self._executed = True
        return self._result

    def __repr__(self):
        return f"<DockerFileRequest src={self.src_path} dst={self.dst_path} container={self.container} to_container={self.to_container}>" 