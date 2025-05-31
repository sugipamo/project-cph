from src.operations.result import OperationResult
from src.operations.docker.docker_driver import DockerDriver

class MockDockerDriver(DockerDriver):
    def __init__(self):
        self.operations = []

    def run_container(self, image: str, name: str = None, options=None, show_output: bool = True):
        self.operations.append(("run", image, name, options, show_output))
        return OperationResult(stdout=f"mock_container_{name or image}")

    def stop_container(self, name: str, show_output: bool = True):
        self.operations.append(("stop", name, show_output))
        return OperationResult(stdout=None)

    def remove_container(self, name: str, show_output: bool = True):
        self.operations.append(("remove", name, show_output))
        return OperationResult(stdout=None)

    def exec_in_container(self, name: str, command: str, show_output: bool = True):
        self.operations.append(("exec", name, command, show_output))
        return OperationResult(stdout=f"mock_exec_result_{name}_{command}")

    def get_logs(self, name: str, show_output: bool = True):
        self.operations.append(("logs", name, show_output))
        return OperationResult(stdout=f"mock_logs_{name}")

    def build(self, path: str, tag: str = None, dockerfile: str = None, options=None, show_output: bool = True):
        self.operations.append(("build", path, tag, dockerfile, options, show_output))
        return f"mock_build_{tag or path}"

    def image_ls(self, show_output: bool = True):
        self.operations.append(("image_ls", show_output))
        return ["mock_image1", "mock_image2"]

    def image_rm(self, image: str, show_output: bool = True):
        self.operations.append(("image_rm", image, show_output))
        return f"mock_rm_{image}"

    def ps(self, all: bool = False, show_output: bool = True):
        self.operations.append(("ps", all, show_output))
        return ["mock_container1", "mock_container2"]

    def inspect(self, target: str, type_: str = None, show_output: bool = True):
        self.operations.append(("inspect", target, type_, show_output))
        return {"mock_inspect": target, "type": type_}

    def cp(self, src: str, dst: str, container: str, to_container: bool = True, show_output: bool = True):
        self.operations.append(("cp", src, dst, container, to_container, show_output))
        return f"mock_cp_{src}_{dst}_{container}_{to_container}"

 