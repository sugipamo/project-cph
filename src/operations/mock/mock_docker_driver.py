from src.operations.result import OperationResult
from src.operations.docker.docker_driver import DockerDriver

class MockDockerDriver(DockerDriver):
    def __init__(self):
        self.operations = []

    def run_container(self, image: str, name: str = None, options=None):
        self.operations.append(("run", image, name, options))
        return OperationResult(stdout=f"mock_container_{name or image}")

    def stop_container(self, name: str):
        self.operations.append(("stop", name))
        return OperationResult(stdout=None)

    def remove_container(self, name: str):
        self.operations.append(("remove", name))
        return OperationResult(stdout=None)

    def exec_in_container(self, name: str, command: str):
        self.operations.append(("exec", name, command))
        return OperationResult(stdout=f"mock_exec_result_{name}_{command}")

    def get_logs(self, name: str):
        self.operations.append(("logs", name))
        return OperationResult(stdout=f"mock_logs_{name}")

    def build(self, path: str, tag: str = None, dockerfile: str = None, options=None):
        self.operations.append(("build", path, tag, dockerfile, options))
        return f"mock_build_{tag or path}"

    def image_ls(self):
        self.operations.append(("image_ls",))
        return ["mock_image1", "mock_image2"]

    def image_rm(self, image: str):
        self.operations.append(("image_rm", image))
        return f"mock_rm_{image}"

    def ps(self, all: bool = False):
        self.operations.append(("ps", all))
        return ["mock_container1", "mock_container2"]

    def inspect(self, target: str, type_: str = None):
        self.operations.append(("inspect", target, type_))
        return {"mock_inspect": target, "type": type_}

    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        self.operations.append(("cp", src, dst, container, to_container))
        return f"mock_cp_{src}_{dst}_{container}_{to_container}"

class DummyDockerDriver(DockerDriver):
    def run_container(self, image: str, name: str = None, options=None):
        return None
    def stop_container(self, name: str):
        return None
    def remove_container(self, name: str):
        return None
    def exec_in_container(self, name: str, command: str):
        return None
    def get_logs(self, name: str):
        return None
    def build(self, path: str, tag: str = None, dockerfile: str = None, options=None):
        return None
    def image_ls(self):
        return []
    def image_rm(self, image: str):
        return None
    def ps(self, all: bool = False):
        return []
    def inspect(self, target: str, type_: str = None):
        return None
    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        return None 