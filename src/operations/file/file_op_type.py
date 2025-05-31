"""
File operation types
"""
from enum import Enum, auto


class FileOpType(Enum):
    READ = auto()
    WRITE = auto()
    EXISTS = auto()
    MOVE = auto()
    COPY = auto()
    COPYTREE = auto()
    REMOVE = auto()
    RMTREE = auto()
    MKDIR = auto()
    TOUCH = auto()