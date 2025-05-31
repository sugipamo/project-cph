"""
Request builder registry
"""
from typing import Dict, Optional
from ..command_types import CommandType
from .base_builder import RequestBuilder
from .file_request_builder import FileRequestBuilder
from .shell_request_builder import ShellRequestBuilder
from .python_request_builder import PythonRequestBuilder
from .docker_request_builder import DockerRequestBuilder


class RequestBuilderRegistry:
    """Registry for request builders"""
    
    def __init__(self):
        self._builders: Dict[CommandType, RequestBuilder] = {}
        self._initialize_default_builders()
    
    def _initialize_default_builders(self):
        """Initialize default builders"""
        self.register(CommandType.FILE, FileRequestBuilder())
        self.register(CommandType.SHELL, ShellRequestBuilder())
        self.register(CommandType.PYTHON, PythonRequestBuilder())
        self.register(CommandType.DOCKER, DockerRequestBuilder())
    
    def register(self, command_type: CommandType, builder: RequestBuilder):
        """Register a builder for a command type"""
        self._builders[command_type] = builder
    
    def get_builder(self, command_type: CommandType) -> Optional[RequestBuilder]:
        """Get builder for command type"""
        return self._builders.get(command_type)
    
    def unregister(self, command_type: CommandType):
        """Unregister a builder"""
        if command_type in self._builders:
            del self._builders[command_type]
    
    def list_registered_types(self) -> list:
        """List all registered command types"""
        return list(self._builders.keys())
    
    def has_builder(self, command_type: CommandType) -> bool:
        """Check if builder is registered for command type"""
        return command_type in self._builders