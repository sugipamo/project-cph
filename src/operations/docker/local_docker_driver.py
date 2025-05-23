from typing import Any, Dict
from src.operations.docker.docker_driver import DockerDriver
from src.operations.shell.shell_request import ShellRequest
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_util import DockerUtil

class LocalDockerDriver(DockerDriver):
    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None):
        base_cmd = ["docker", "run", "-d"]
        opt = dict(options) if options else {}
        if name:
            opt["name"] = name
        cmd = DockerUtil.build_docker_cmd(base_cmd, options=opt, positional_args=[image])
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def stop_container(self, name: str):
        cmd = ["docker", "stop", name]
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def remove_container(self, name: str):
        cmd = ["docker", "rm", name]
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def exec_in_container(self, name: str, command: str):
        cmd = ["docker", "exec", name] + command.split()
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def get_logs(self, name: str):
        cmd = ["docker", "logs", name]
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def build(self, path: str, tag: str = None, dockerfile: str = None, options: Dict[str, Any] = None):
        base_cmd = ["docker", "build"]
        opt = dict(options) if options else {}
        if tag:
            opt["t"] = tag
        if dockerfile:
            opt["f"] = dockerfile
        cmd = DockerUtil.build_docker_cmd(base_cmd, options=opt, positional_args=[path])
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def image_ls(self):
        cmd = ["docker", "image", "ls"]
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def image_rm(self, image: str):
        cmd = ["docker", "image", "rm", image]
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def ps(self, all: bool = False):
        cmd = ["docker", "ps"]
        if all:
            cmd.append("-a")
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def inspect(self, target: str, type_: str = None):
        cmd = ["docker", "inspect"]
        if type_:
            cmd += ["--type", type_]
        cmd.append(target)
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result

    def cp(self, src: str, dst: str, container: str, to_container: bool = True):
        if to_container:
            cp_src = str(src)
            cp_dst = f"{container}:{dst}"
        else:
            cp_src = f"{container}:{src}"
            cp_dst = str(dst)
        cmd = ["docker", "cp", cp_src, cp_dst]
        req = ShellRequest(cmd)
        result = req.execute(driver=LocalShellDriver())
        return result 