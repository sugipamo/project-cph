"""
Unified command request factory

Consolidates multiple factory classes into a single, configurable factory
with reduced code duplication and improved maintainability.
"""

from typing import Dict, Any, Optional, Union
from .base.factory import BaseCommandRequestFactory
from .command_types import CommandType, get_command_type_from_string, get_command_config
from .request_builders import RequestBuilderRegistry
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class UnifiedCommandRequestFactory(BaseCommandRequestFactory):
    """
    Unified factory for creating command requests
    
    Replaces multiple specialized factory classes with a single,
    configuration-driven approach.
    """
    
    def __init__(self, controller):
        super().__init__(controller)
        self.builder_registry = RequestBuilderRegistry()
        self._initialize_builders()
    
    def _initialize_builders(self):
        """Initialize request builders for different command types"""
        # Register builders for each command type
        from .request_builders import (
            ShellRequestBuilder,
            FileRequestBuilder, 
            PythonRequestBuilder,
            DockerRequestBuilder
        )
        
        self.builder_registry.register(CommandType.SHELL, ShellRequestBuilder())
        self.builder_registry.register(CommandType.COPY, FileRequestBuilder(FileOpType.COPY))
        self.builder_registry.register(CommandType.MKDIR, FileRequestBuilder(FileOpType.MKDIR))
        self.builder_registry.register(CommandType.TOUCH, FileRequestBuilder(FileOpType.TOUCH))
        self.builder_registry.register(CommandType.REMOVE, FileRequestBuilder(FileOpType.REMOVE))
        self.builder_registry.register(CommandType.RMTREE, FileRequestBuilder(FileOpType.RMTREE))
        self.builder_registry.register(CommandType.MOVE, FileRequestBuilder(FileOpType.MOVE))
        self.builder_registry.register(CommandType.MOVETREE, FileRequestBuilder(FileOpType.COPYTREE))
        self.builder_registry.register(CommandType.PYTHON, PythonRequestBuilder())
        self.builder_registry.register(CommandType.DOCKER, DockerRequestBuilder())
        self.builder_registry.register(CommandType.BUILD, DockerRequestBuilder())
        self.builder_registry.register(CommandType.OJ, ShellRequestBuilder())  # OJ uses shell execution
    
    def create_request(self, run_step):
        """Create request from run step"""
        command_type = self._get_command_type_from_step(run_step)
        if not command_type:
            raise ValueError(f"Unsupported step type: {type(run_step).__name__}")
        
        builder = self.builder_registry.get_builder(command_type)
        if not builder:
            raise ValueError(f"No builder registered for command type: {command_type}")
        
        return builder.build_from_step(run_step, self)
    
    def create_request_from_node(self, node):
        """Create request from ConfigNode"""
        if not node.value or not isinstance(node.value, dict):
            raise ValueError("Invalid node value for UnifiedCommandRequestFactory")
        
        type_str = node.value.get('type')
        if not type_str:
            raise ValueError("Missing 'type' field in node value")
        
        command_type = get_command_type_from_string(type_str)
        if not command_type:
            raise ValueError(f"Unsupported command type: {type_str}")
        
        builder = self.builder_registry.get_builder(command_type)
        if not builder:
            raise ValueError(f"No builder registered for command type: {command_type}")
        
        return builder.build_from_node(node, self)
    
    def create_request_by_type(self, command_type: CommandType, **kwargs):
        """Create request by command type with keyword arguments"""
        builder = self.builder_registry.get_builder(command_type)
        if not builder:
            raise ValueError(f"No builder registered for command type: {command_type}")
        
        return builder.build_from_kwargs(kwargs, self)
    
    def _get_command_type_from_step(self, run_step) -> Optional[CommandType]:
        """Extract command type from run step class name"""
        class_name = type(run_step).__name__
        
        # Map step class names to command types
        step_type_mapping = {
            'ShellRunStep': CommandType.SHELL,
            'CopyRunStep': CommandType.COPY,
            'MkdirRunStep': CommandType.MKDIR,
            'TouchRunStep': CommandType.TOUCH,
            'RemoveRunStep': CommandType.REMOVE,
            'RmtreeRunStep': CommandType.RMTREE,
            'MoveRunStep': CommandType.MOVE,
            'MovetreeRunStep': CommandType.MOVETREE,
            'PythonRunStep': CommandType.PYTHON,
            'DockerRunStep': CommandType.DOCKER,
            'BuildRunStep': CommandType.BUILD,
            'OjRunStep': CommandType.OJ
        }
        
        return step_type_mapping.get(class_name)
    
    def supports_command_type(self, command_type: Union[str, CommandType]) -> bool:
        """Check if command type is supported"""
        if isinstance(command_type, str):
            command_type = get_command_type_from_string(command_type)
        
        return command_type and self.builder_registry.has_builder(command_type)
    
    def get_supported_types(self) -> list:
        """Get list of supported command types"""
        return list(self.builder_registry.get_registered_types())