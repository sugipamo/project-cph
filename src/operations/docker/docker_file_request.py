from src.operations.result import OperationResult
import time

class DockerFileRequest:
    def __init__(self, src_path, dst_path, container, to_container=True, docker_driver=None):
        self.src_path = src_path
        self.dst_path = dst_path
        self.container = container
        self.to_container = to_container
        self.docker_driver = docker_driver
        self._executed = False
        self._result = None

    def execute(self):
        if self._executed:
            raise RuntimeError("This DockerFileRequest has already been executed.")
        start_time = time.time()
        try:
            if self.docker_driver is None:
                raise ValueError("docker_driverが必要です")
            self.docker_driver.cp(self.src_path, self.dst_path, self.container, to_container=self.to_container)
            self._result = OperationResult(success=True, path=self.src_path, op="DOCKER_CP", request=self, start_time=start_time, end_time=time.time())
        except Exception as e:
            self._result = OperationResult(success=False, path=self.src_path, op="DOCKER_CP", request=self, start_time=start_time, end_time=time.time(), error_message=str(e), exception=e)
            self._executed = True
            raise
        self._executed = True
        return self._result 