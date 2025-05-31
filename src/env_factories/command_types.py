"""
Command type definitions for unified factory pattern
"""

from enum import Enum
from typing import Dict, Any, Type, Optional


class CommandType(Enum):
    """Command types supported by the unified factory"""
    SHELL = "shell"
    DOCKER = "docker"
    COPY = "copy"
    BUILD = "build"
    PYTHON = "python"
    OJ = "oj"
    MKDIR = "mkdir"
    TOUCH = "touch"
    REMOVE = "remove"
    RMTREE = "rmtree"
    MOVE = "move"
    MOVETREE = "movetree"


class CommandConfig:
    """Configuration for command request creation"""
    
    def __init__(self, 
                 command_type: CommandType,
                 request_class: Type,
                 required_fields: list = None,
                 default_values: Dict[str, Any] = None):
        self.command_type = command_type
        self.request_class = request_class
        self.required_fields = required_fields or []
        self.default_values = default_values or {}


# Command configurations registry
COMMAND_CONFIGS: Dict[CommandType, CommandConfig] = {}


def register_command_config(config: CommandConfig):
    """Register a command configuration"""
    COMMAND_CONFIGS[config.command_type] = config


def get_command_config(command_type: CommandType) -> Optional[CommandConfig]:
    """Get command configuration by type"""
    return COMMAND_CONFIGS.get(command_type)


def get_command_type_from_string(type_str: str) -> Optional[CommandType]:
    """Convert string to CommandType"""
    try:
        return CommandType(type_str.lower())
    except ValueError:
        return None