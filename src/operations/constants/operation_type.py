from enum import Enum, auto

class OperationType(Enum):
    SHELL = auto()
    FILE = auto()
    DOCKER = auto()
    COMPOSITE = auto()
    PYTHON = auto() 