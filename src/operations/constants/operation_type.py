from enum import Enum, auto

class OperationType(Enum):
    SHELL = auto()
    SHELL_INTERACTIVE = auto()
    FILE = auto()
    DOCKER = auto()
    COMPOSITE = auto()
    PYTHON = auto() 