from abc import ABC, abstractmethod
from typing import Any, Optional, List, Dict
import subprocess

class AbstractExecutionClient(ABC):
    @abstractmethod
    def run(self, name: str, image: Optional[str] = None, command: Optional[List[str]] = None, volumes: Optional[Dict[str, str]] = None, detach: bool = True, **kwargs) -> Any:
        pass

    @abstractmethod
    def stop(self, name: str) -> bool:
        pass

    @abstractmethod
    def remove(self, name: str) -> bool:
        pass

    @abstractmethod
    def exec_in(self, name: str, cmd: List[str], **kwargs) -> subprocess.CompletedProcess:
        pass

    @abstractmethod
    def is_running(self, name: str) -> bool:
        pass

    @abstractmethod
    def list(self, all: bool = True, prefix: Optional[str] = None) -> List[str]:
        pass 