from abc import ABC, abstractmethod
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from src.shell_process import ShellProcess, ShellProcessOptions


class BaseRunHandler(ABC):
    def __init__(self, config: dict):
        self.config = config

    @abstractmethod
    def run(self, cmd: List[str]) -> ShellProcess:
        pass

class LocalRunHandler(BaseRunHandler):
    pass

class DockerRunHandler(BaseRunHandler):
    pass