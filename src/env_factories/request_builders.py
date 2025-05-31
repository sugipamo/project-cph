"""
Request builders for the unified factory pattern

Each builder handles the creation of specific request types
with their unique logic while sharing common patterns.
"""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional
from .command_types import CommandType
from src.operations.file.file_request import FileRequest, FileOpType
from src.operations.shell.shell_request import ShellRequest
from src.operations.python.python_request import PythonRequest
from src.operations.docker.docker_request import DockerRequest, DockerOpType


class RequestBuilder(ABC):
    """Base class for request builders"""
    
    @abstractmethod
    def build_from_step(self, run_step, factory):
        """Build request from run step"""
        pass
    
    @abstractmethod
    def build_from_node(self, node, factory):
        """Build request from ConfigNode"""
        pass
    
    @abstractmethod
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build request from keyword arguments"""
        pass


class RequestBuilderRegistry:
    """Registry for request builders"""
    
    def __init__(self):
        self._builders: Dict[CommandType, RequestBuilder] = {}
    
    def register(self, command_type: CommandType, builder: RequestBuilder):
        """Register a builder for a command type"""
        self._builders[command_type] = builder
    
    def get_builder(self, command_type: CommandType) -> Optional[RequestBuilder]:
        """Get builder for command type"""
        return self._builders.get(command_type)
    
    def has_builder(self, command_type: CommandType) -> bool:
        """Check if builder exists for command type"""
        return command_type in self._builders
    
    def get_registered_types(self) -> list:
        """Get list of registered command types"""
        return list(self._builders.keys())


class ShellRequestBuilder(RequestBuilder):
    """Builder for shell requests"""
    
    def build_from_step(self, run_step, factory):
        """Build ShellRequest from run step"""
        cmd = [factory.format_string(arg) for arg in run_step.cmd]
        cwd = factory.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        request = ShellRequest(cmd, cwd=cwd, show_output=getattr(run_step, 'show_output', True))
        request.allow_failure = getattr(run_step, 'allow_failure', False)
        return request
    
    def build_from_node(self, node, factory):
        """Build ShellRequest from ConfigNode"""
        cmd = node.value.get('cmd', [])
        cwd = node.value.get('cwd')
        show_output = node.value.get('show_output', True)
        allow_failure = node.value.get('allow_failure', False)
        
        # Format cmd array with node-specific formatting
        formatted_cmd = self._format_cmd_array(cmd, node, factory)
        
        # Format cwd if provided
        formatted_cwd = None
        if cwd:
            cwd_node = self._find_child_node(node, 'cwd')
            formatted_cwd = factory.format_value(cwd, cwd_node if cwd_node else node)
        
        request = ShellRequest(formatted_cmd, cwd=formatted_cwd, show_output=show_output)
        request.allow_failure = allow_failure
        return request
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build ShellRequest from kwargs"""
        cmd = kwargs.get('cmd', [])
        cwd = kwargs.get('cwd')
        show_output = kwargs.get('show_output', True)
        
        request = ShellRequest(cmd, cwd=cwd, show_output=show_output)
        request.allow_failure = kwargs.get('allow_failure', False)
        return request
    
    def _format_cmd_array(self, cmd, node, factory):
        """Format command array with proper node context"""
        cmd_node = self._find_child_node(node, 'cmd')
        formatted_cmd = []
        
        if cmd_node and cmd_node.next_nodes:
            for i, arg in enumerate(cmd):
                arg_node = self._find_child_node(cmd_node, i)
                if arg_node:
                    formatted_cmd.append(factory.format_value(arg, arg_node))
                else:
                    formatted_cmd.append(factory.format_value(arg, node))
        else:
            formatted_cmd = [factory.format_value(arg, node) for arg in cmd]
        
        return formatted_cmd
    
    def _find_child_node(self, parent_node, key):
        """Find child node by key"""
        for child in parent_node.next_nodes:
            if child.key == key:
                return child
        return None


class FileRequestBuilder(RequestBuilder):
    """Builder for file operation requests"""
    
    def __init__(self, file_op_type: FileOpType):
        self.file_op_type = file_op_type
    
    def build_from_step(self, run_step, factory):
        """Build FileRequest from run step"""
        if self.file_op_type in [FileOpType.COPY, FileOpType.MOVE, FileOpType.COPYTREE]:
            return self._build_two_path_request(run_step, factory)
        else:
            return self._build_single_path_request(run_step, factory)
    
    def build_from_node(self, node, factory):
        """Build FileRequest from ConfigNode"""
        if self.file_op_type in [FileOpType.COPY, FileOpType.MOVE, FileOpType.COPYTREE]:
            return self._build_two_path_request_from_node(node, factory)
        else:
            return self._build_single_path_request_from_node(node, factory)
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build FileRequest from kwargs"""
        if self.file_op_type in [FileOpType.COPY, FileOpType.MOVE, FileOpType.COPYTREE]:
            src = kwargs.get('src') or kwargs.get('source')
            dst = kwargs.get('dst') or kwargs.get('destination') or kwargs.get('target')
            if not src or not dst:
                raise ValueError(f"Both 'src' and 'dst' required for {self.file_op_type}")
            request = FileRequest(self.file_op_type, src, dst_path=dst)
        else:
            path = kwargs.get('path') or kwargs.get('target')
            if not path:
                raise ValueError(f"'path' required for {self.file_op_type}")
            request = FileRequest(self.file_op_type, path)
        
        request.allow_failure = kwargs.get('allow_failure', False)
        return request
    
    def _build_two_path_request(self, run_step, factory):
        """Build request requiring source and destination paths"""
        if len(run_step.cmd) < 2:
            raise ValueError(f"{self.file_op_type}: cmd requires src and dst paths")
        
        src = factory.format_string(run_step.cmd[0])
        dst = factory.format_string(run_step.cmd[1])
        request = FileRequest(self.file_op_type, src, dst_path=dst)
        request.allow_failure = getattr(run_step, 'allow_failure', False)
        return request
    
    def _build_single_path_request(self, run_step, factory):
        """Build request requiring single path"""
        if not run_step.cmd:
            raise ValueError(f"{self.file_op_type}: cmd requires target path")
        
        target = factory.format_string(run_step.cmd[0])
        request = FileRequest(self.file_op_type, target)
        request.allow_failure = getattr(run_step, 'allow_failure', False)
        return request
    
    def _build_two_path_request_from_node(self, node, factory):
        """Build two-path request from ConfigNode"""
        cmd = node.value.get('cmd', [])
        if len(cmd) < 2:
            raise ValueError(f"{self.file_op_type}: cmd requires src and dst paths")
        
        cmd_node = self._find_child_node(node, 'cmd')
        if cmd_node and len(cmd_node.next_nodes) >= 2:
            src_node = cmd_node.next_nodes[0]
            dst_node = cmd_node.next_nodes[1]
            src = factory.format_value(cmd[0], src_node)
            dst = factory.format_value(cmd[1], dst_node)
        else:
            src = factory.format_value(cmd[0], node)
            dst = factory.format_value(cmd[1], node)
        
        request = FileRequest(self.file_op_type, src, dst_path=dst)
        request.allow_failure = node.value.get('allow_failure', False)
        return request
    
    def _build_single_path_request_from_node(self, node, factory):
        """Build single-path request from ConfigNode"""
        cmd = node.value.get('cmd', [])
        if not cmd:
            raise ValueError(f"{self.file_op_type}: cmd requires target path")
        
        cmd_node = self._find_child_node(node, 'cmd')
        if cmd_node and cmd_node.next_nodes:
            target_node = cmd_node.next_nodes[0]
            target = factory.format_value(cmd[0], target_node)
        else:
            target = factory.format_value(cmd[0], node)
        
        request = FileRequest(self.file_op_type, target)
        request.allow_failure = node.value.get('allow_failure', False)
        return request
    
    def _find_child_node(self, parent_node, key):
        """Find child node by key"""
        for child in parent_node.next_nodes:
            if child.key == key:
                return child
        return None


class PythonRequestBuilder(RequestBuilder):
    """Builder for Python requests"""
    
    def build_from_step(self, run_step, factory):
        """Build PythonRequest from run step"""
        code_or_file = [factory.format_string(arg) for arg in run_step.cmd]
        cwd = factory.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        request = PythonRequest(code_or_file, cwd=cwd, show_output=getattr(run_step, 'show_output', True))
        request.allow_failure = getattr(run_step, 'allow_failure', False)
        return request
    
    def build_from_node(self, node, factory):
        """Build PythonRequest from ConfigNode"""
        cmd = node.value.get('cmd', [])
        cwd = node.value.get('cwd')
        show_output = node.value.get('show_output', True)
        
        # Format cmd array
        formatted_cmd = []
        cmd_node = self._find_child_node(node, 'cmd')
        if cmd_node and cmd_node.next_nodes:
            for i, arg in enumerate(cmd):
                arg_node = self._find_child_node(cmd_node, i)
                if arg_node:
                    formatted_cmd.append(factory.format_value(arg, arg_node))
                else:
                    formatted_cmd.append(factory.format_value(arg, node))
        else:
            formatted_cmd = [factory.format_value(arg, node) for arg in cmd]
        
        # Format cwd
        formatted_cwd = None
        if cwd:
            cwd_node = self._find_child_node(node, 'cwd')
            formatted_cwd = factory.format_value(cwd, cwd_node if cwd_node else node)
        
        request = PythonRequest(formatted_cmd, cwd=formatted_cwd, show_output=show_output)
        request.allow_failure = node.value.get('allow_failure', False)
        return request
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build PythonRequest from kwargs"""
        code_or_file = kwargs.get('code_or_file', kwargs.get('cmd', []))
        cwd = kwargs.get('cwd')
        show_output = kwargs.get('show_output', True)
        
        request = PythonRequest(code_or_file, cwd=cwd, show_output=show_output)
        request.allow_failure = kwargs.get('allow_failure', False)
        return request
    
    def _find_child_node(self, parent_node, key):
        """Find child node by key"""
        for child in parent_node.next_nodes:
            if child.key == key:
                return child
        return None


class DockerRequestBuilder(RequestBuilder):
    """Builder for Docker requests"""
    
    def build_from_step(self, run_step, factory):
        """Build DockerRequest from run step"""
        # Docker implementation depends on the specific step type
        op_type = self._determine_docker_op_type(run_step)
        
        if op_type == DockerOpType.RUN:
            image = factory.format_string(run_step.cmd[0]) if run_step.cmd else None
            request = DockerRequest(op_type, image=image)
        elif op_type == DockerOpType.BUILD:
            dockerfile_path = factory.format_string(run_step.cmd[0]) if run_step.cmd else None
            request = DockerRequest(op_type, dockerfile_path=dockerfile_path)
        else:
            request = DockerRequest(op_type)
        
        request.allow_failure = getattr(run_step, 'allow_failure', False)
        return request
    
    def build_from_node(self, node, factory):
        """Build DockerRequest from ConfigNode"""
        cmd = node.value.get('cmd', [])
        docker_type = node.value.get('docker_type', 'run')
        
        op_type = DockerOpType.RUN if docker_type == 'run' else DockerOpType.BUILD
        
        if op_type == DockerOpType.RUN and cmd:
            image = factory.format_value(cmd[0], node)
            request = DockerRequest(op_type, image=image)
        elif op_type == DockerOpType.BUILD and cmd:
            dockerfile_path = factory.format_value(cmd[0], node)
            request = DockerRequest(op_type, dockerfile_path=dockerfile_path)
        else:
            request = DockerRequest(op_type)
        
        request.allow_failure = node.value.get('allow_failure', False)
        return request
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build DockerRequest from kwargs"""
        op_type = kwargs.get('op_type', DockerOpType.RUN)
        image = kwargs.get('image')
        dockerfile_path = kwargs.get('dockerfile_path')
        
        request = DockerRequest(op_type, image=image, dockerfile_path=dockerfile_path)
        request.allow_failure = kwargs.get('allow_failure', False)
        return request
    
    def _determine_docker_op_type(self, run_step):
        """Determine Docker operation type from run step"""
        class_name = type(run_step).__name__
        if 'Build' in class_name:
            return DockerOpType.BUILD
        return DockerOpType.RUN