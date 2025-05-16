"""
docker_driver.py
operations層のDockerRequest等から利用される、docker操作の実体（バックエンド）実装。
ローカル・モック・ダミーなど複数の実装を提供する。
"""
from abc import ABC, abstractmethod
from typing import Any, Dict

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

class LocalDockerDriver(DockerDriver):
    def run_container(self, image: str, name: str = None, options: Dict[str, Any] = None):
        # 実際にdockerコマンドを叩く実装（仮）
        # 例: subprocess.run(["docker", "run", ...])
        pass

    def stop_container(self, name: str):
        pass

    def remove_container(self, name: str):
        pass

    def exec_in_container(self, name: str, command: str):
        pass

    def get_logs(self, name: str):
        pass

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