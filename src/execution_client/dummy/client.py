from execution_client.abstract_client import AbstractExecutionClient
from typing import Any, Optional, List, Dict
import subprocess

class DummyExecutionClient(AbstractExecutionClient):
    def run(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, **kwargs) -> Any:
        raise NotImplementedError

    def stop(self, name: str) -> bool:
        raise NotImplementedError

    def remove(self, name: str) -> bool:
        raise NotImplementedError

    def exec_in(self, name: str, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        raise NotImplementedError

    def is_running(self, name: str) -> bool:
        raise NotImplementedError

    def list(self, all: bool = True, prefix: Optional[str] = None) -> List[str]:
        raise NotImplementedError 