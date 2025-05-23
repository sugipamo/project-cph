from typing import Any, Dict
from src.operations.docker.docker_driver import DockerDriver

class DummyDockerDriver(DockerDriver):
    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None):
        return None

    def stop_container(self, name: str):
        pass

    def remove_container(self, name: str):
        pass

    def exec_in_container(self, name: str, command: str):
        return None

    def get_logs(self, name: str):
        return None

    def build(self, path: str, tag: str = None, dockerfile: str = None, options: Dict[str, Any] = None):
        return None

    def image_ls(self):
        return []

    def image_rm(self, image: str):
        return None

    def ps(self, all: bool = False):
        return []

    def inspect(self, target: str, type_: str = None):
        pass

    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        pass 