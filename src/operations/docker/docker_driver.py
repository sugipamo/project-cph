"""
docker_driver.py
operations層のDockerRequest等から利用される、docker操作の実体（バックエンド）実装。
ローカル・モック・ダミーなど複数の実装を提供する。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict
from src.operations.shell.shell_request import ShellRequest
from src.operations.result.shell_result import ShellResult
from src.operations.result.result import OperationResult
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_util import DockerUtil

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
    def ps(self, all: bool = False, show_output: bool = True, names_only: bool = False):
        pass

    @abstractmethod
    def inspect(self, target: str, type_: str = None):
        pass

    @abstractmethod
    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        pass

class LocalDockerDriver(DockerDriver):
    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None, show_output: bool = True):
        base_cmd = ["docker", "run", "-d"]
        opt = dict(options) if options else {}
        if name:
            opt["name"] = name
        container_name = name
        if container_name:
            inspect_cmd = ["docker", "inspect", container_name]
            inspect_req = ShellRequest(inspect_cmd, show_output=False)
            inspect_result = inspect_req.execute(driver=LocalShellDriver())
            import json
            try:
                inspect_data = json.loads(inspect_result.stdout)
                if isinstance(inspect_data, list) and len(inspect_data) > 0:
                    state = inspect_data[0].get("State", {})
                    status = state.get("Status", "")
                    if status == "running":
                        return inspect_result
                    else:
                        rm_cmd = ["docker", "rm", container_name]
                        rm_req = ShellRequest(rm_cmd, show_output=False)
                        rm_req.execute(driver=LocalShellDriver())
            except Exception:
                pass
        positional_args = [image, "tail", "-f", "/dev/null"]
        cmd = DockerUtil.build_docker_cmd(base_cmd, options=opt, positional_args=positional_args)
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def stop_container(self, name: str, show_output: bool = True):
        cmd = ["docker", "stop", name]
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def remove_container(self, name: str, show_output: bool = True):
        cmd = ["docker", "rm", name]
        req = ShellRequest(cmd, show_output=False)
        result = req.execute(driver=LocalShellDriver())
        return result

    def exec_in_container(self, name: str, command: str, show_output: bool = True):
        cmd = ["docker", "exec", name] + command.split()
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def get_logs(self, name: str, show_output: bool = True):
        cmd = ["docker", "logs", name]
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def build(self, path: str, tag: str = None, dockerfile: str = None, options: Dict[str, Any] = None, show_output: bool = True):
        base_cmd = ["docker", "build"]
        opt = dict(options) if options else {}
        inputdata = opt.pop('inputdata', None)
        if tag:
            opt["t"] = tag
        if dockerfile:
            opt["f"] = dockerfile
        cmd = DockerUtil.build_docker_cmd(base_cmd, options=opt, positional_args=[path])
        req = ShellRequest(cmd, show_output=show_output, inputdata=inputdata)
        result = req.execute(driver=LocalShellDriver())
        return result

    def image_ls(self, show_output: bool = True):
        cmd = ["docker", "image", "ls"]
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def image_rm(self, image: str, show_output: bool = True):
        cmd = ["docker", "image", "rm", image]
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def ps(self, all: bool = False, show_output: bool = True, names_only: bool = False):
        if names_only:
            cmd = ["docker", "ps", "-a", "--format", "{{.Names}}"]
            req = ShellRequest(cmd, show_output=show_output)
            result = req.execute(driver=LocalShellDriver())
            names = result.stdout.strip().split("\n") if result.stdout else []
            return names
        else:
            cmd = ["docker", "ps"]
            if all:
                cmd.append("-a")
            req = ShellRequest(cmd, show_output=show_output)
            result = req.execute(driver=LocalShellDriver())
            return result

    def inspect(self, target: str, type_: str = None, show_output: bool = True):
        cmd = ["docker", "inspect"]
        if type_:
            cmd += ["--type", type_]
        cmd.append(target)
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def cp(self, src: str, dst: str, container: str, to_container: bool = True, show_output: bool = True):
        if to_container:
            cp_src = str(src)
            cp_dst = f"{container}:{dst}"
        else:
            cp_src = f"{container}:{src}"
            cp_dst = str(dst)
        cmd = ["docker", "cp", cp_src, cp_dst]
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

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