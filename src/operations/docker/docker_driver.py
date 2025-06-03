"""
docker_driver.py
operations層のDockerRequest等から利用される、docker操作の実体（バックエンド）実装。
ローカル・モック・ダミーなど複数の実装を提供する。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Union, List
from src.operations.shell.shell_request import ShellRequest
from src.operations.shell.local_shell_driver import LocalShellDriver
from src.operations.docker.docker_utils import DockerUtils
from src.operations.utils.pure_functions import (
    build_docker_run_command_pure,
    build_docker_build_command_pure,
    build_docker_stop_command_pure,
    build_docker_remove_command_pure,
    build_docker_ps_command_pure,
    build_docker_inspect_command_pure,
    build_docker_cp_command_pure,
    parse_container_names_pure,
    validate_docker_image_name_pure
)

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
    def remove_container(self, name: str, force: bool = False):
        pass

    @abstractmethod
    def exec_in_container(self, name: str, command: Union[str, List[str]]):
        pass

    @abstractmethod
    def get_logs(self, name: str):
        pass

    @abstractmethod
    def build(self, tag: str = None, options: Dict[str, Any] = None, show_output: bool = True, dockerfile_text: str = None):
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
        # 純粋関数を使用してコマンドを構築
        cmd = build_docker_run_command_pure(image, name, options)
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def stop_container(self, name: str, show_output: bool = True):
        cmd = build_docker_stop_command_pure(name)
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def remove_container(self, name: str, force: bool = False, show_output: bool = True):
        cmd = build_docker_remove_command_pure(name, force=force)
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def exec_in_container(self, name: str, command: Union[str, List[str]], show_output: bool = True):
        # セキュリティ強化: 全てのコマンドを統一的にshlex.splitで処理
        import shlex
        
        if isinstance(command, list):
            # コマンドが既にリスト形式の場合はそのまま使用
            cmd = ["docker", "exec", name] + command
        elif isinstance(command, str):
            # 文字列の場合は常にshlex.splitを使用して安全に解析
            # bash -c の特殊処理を削除し、統一的な処理に変更
            cmd_parts = shlex.split(command)
            cmd = ["docker", "exec", name] + cmd_parts
        else:
            raise ValueError(f"Invalid command type: {type(command)}")
        
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def get_logs(self, name: str, show_output: bool = True):
        cmd = ["docker", "logs", name]
        req = ShellRequest(cmd, show_output=show_output)
        result = req.execute(driver=LocalShellDriver())
        return result

    def build(self, dockerfile_text: str, tag: str = None, options: Dict[str, Any] = None, show_output: bool = True):
        if not dockerfile_text or dockerfile_text is None:
            raise ValueError("dockerfile_text is None. Dockerfile内容が正しく渡っていません。")
        
        # 純粋関数を使用してコマンドを構築
        cmd = build_docker_build_command_pure(tag, dockerfile_text, options)
        req = ShellRequest(cmd, show_output=show_output, inputdata=dockerfile_text)
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
            # 純粋関数を使用してコンテナ名を解析
            return parse_container_names_pure(result.stdout or "")
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

 