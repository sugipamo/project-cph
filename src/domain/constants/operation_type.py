"""Operation type constants."""
from enum import Enum, auto


class OperationType(Enum):
    """Enumeration of operation types."""
    SHELL = auto()
    SHELL_INTERACTIVE = auto()
    FILE = auto()
    DOCKER = auto()
    COMPOSITE = auto()
    PYTHON = auto()
    FILE_PREPARATION = auto()
    STATE_SHOW = auto()
    WORKSPACE = auto()
