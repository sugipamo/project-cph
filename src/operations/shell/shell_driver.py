from abc import ABC, abstractmethod

class ShellDriver(ABC):
    @abstractmethod
    def run(self, cmd, cwd=None, env=None, inputdata=None, timeout=None):
        pass 