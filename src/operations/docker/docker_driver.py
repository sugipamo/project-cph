"""
docker_driver.py
operations層のDockerRequest等から利用される、docker操作の実体（バックエンド）実装。
ローカル・モック・ダミーなど複数の実装を提供する。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.operations.shell.shell_request import ShellRequest
from src.operations.shell.shell_result import ShellResult

class DockerDriver(ABC):
    def __init__(self):
        pass

    @abstractmethod
    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None):
        pass

    @abstractmethod
    def stop_container(self, name: str):
        pass

    @abstractmethod
    def remove_container(self, name: str):
        pass

    @abstractmethod
    def exec_in_container(self, name: str, command: str):
        pass

    @abstractmethod
    def get_logs(self, name: str):
        pass

    @abstractmethod
    def build(self, path: str, tag: str = None, dockerfile: str = None, options: Dict[str, Any] = None):
        pass

    @abstractmethod
    def image_ls(self):
        pass

    @abstractmethod
    def image_rm(self, image: str):
        pass

    @abstractmethod
    def ps(self, all: bool = False):
        pass

    @abstractmethod
    def inspect(self, target: str, type_: str = None):
        pass

class LocalDockerDriver(DockerDriver):
    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None):
        cmd = ["docker", "run", "-d"]
        if name:
            cmd += ["--name", name]
        if options:
            for k, v in options.items():
                if len(k) == 1:
                    cmd.append(f"-{k}")
                else:
                    cmd.append(f"--{k.replace('_','-')}")
                if v is not None:
                    cmd.append(str(v))
        cmd.append(image)
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def stop_container(self, name: str):
        cmd = ["docker", "stop", name]
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def remove_container(self, name: str):
        cmd = ["docker", "rm", name]
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def exec_in_container(self, name: str, command: str):
        cmd = ["docker", "exec", name] + command.split()
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def get_logs(self, name: str):
        cmd = ["docker", "logs", name]
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def build(self, path: str, tag: str = None, dockerfile: str = None, options: Dict[str, Any] = None):
        cmd = ["docker", "build"]
        if tag:
            cmd += ["-t", tag]
        if dockerfile:
            cmd += ["-f", dockerfile]
        if options:
            for k, v in options.items():
                if len(k) == 1:
                    cmd.append(f"-{k}")
                else:
                    cmd.append(f"--{k.replace('_','-')}")
                if v is not None:
                    cmd.append(str(v))
        cmd.append(path)
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def image_ls(self):
        cmd = ["docker", "image", "ls"]
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def image_rm(self, image: str):
        cmd = ["docker", "image", "rm", image]
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def ps(self, all: bool = False):
        cmd = ["docker", "ps"]
        if all:
            cmd.append("-a")
        req = ShellRequest(cmd)
        result = req.execute()
        return result

    def inspect(self, target: str, type_: str = None):
        cmd = ["docker", "inspect"]
        if type_:
            cmd += ["--type", type_]
        cmd.append(target)
        req = ShellRequest(cmd)
        result = req.execute()
        return result

class MockDockerDriver(DockerDriver):
    def __init__(self):
        self.operations = []

    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None):
        self.operations.append(("run", image, name, options))
        return f"mock_container_{name or image}"

    def stop_container(self, name: str):
        self.operations.append(("stop", name))

    def remove_container(self, name: str):
        self.operations.append(("remove", name))

    def exec_in_container(self, name: str, command: str):
        self.operations.append(("exec", name, command))
        return f"mock_exec_result_{name}_{command}"

    def get_logs(self, name: str):
        self.operations.append(("logs", name))
        return f"mock_logs_{name}"

    def build(self, path: str, tag: str = None, dockerfile: str = None, options: Dict[str, Any] = None):
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
        return None 