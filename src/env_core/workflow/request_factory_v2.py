"""
Request factory with environment strategy pattern support
"""
from typing import Optional, List, Dict, Any
from src.env_core.step.step import Step
from src.operations.base_request import BaseRequest
from src.operations.environment.environment_manager import EnvironmentManager
from src.operations.environment.strategy_registry import update_strategy_config


class RequestFactoryV2:
    """
    Factory for creating requests with environment strategy pattern.
    Replaces env_type branching with strategy-based execution.
    """
    
    def __init__(self, context: Any):
        """
        Initialize request factory.
        
        Args:
            context: Execution context
        """
        self.context = context
        self.env_manager = EnvironmentManager.from_context(context)
        self._update_strategy_config()
    
    def _update_strategy_config(self):
        """Update strategy configuration from context"""
        if hasattr(self.context, 'env_json') and self.context.env_json:
            # Extract environment-specific config
            lang_config = self.context.env_json.get(self.context.language, {})
            env_types = lang_config.get('env_types', {})
            
            # Update strategy configurations
            for env_type, config in env_types.items():
                update_strategy_config(env_type, config)
    
    def create_request(self, step: Step) -> Optional[BaseRequest]:
        """
        Create a request from a step using environment strategy.
        
        Args:
            step: Step to convert to request
            
        Returns:
            Request object or None if step should be skipped
        """
        # Check if step should be forced to local
        if self.env_manager.should_force_local(step.__dict__):
            # Temporarily switch to local strategy
            original_env = self.env_manager._env_type
            self.env_manager.switch_strategy('local')
            request = self._create_request_internal(step)
            self.env_manager.switch_strategy(original_env)
            return request
        
        # Create request using current strategy
        return self._create_request_internal(step)
    
    def _create_request_internal(self, step: Step) -> Optional[BaseRequest]:
        """
        Internal method to create request based on step type.
        
        Args:
            step: Step to convert
            
        Returns:
            Request object or None
        """
        # Delegate to specific creation methods based on step type
        creators = {
            'shell': self._create_shell_request,
            'file': self._create_file_request,
            'copy': self._create_copy_request,
            'docker': self._create_docker_request,
            'python': self._create_python_request,
            'test': self._create_test_request,
            'oj': self._create_oj_request,
        }
        
        creator = creators.get(step.type)
        if creator:
            return creator(step)
        
        # Unknown step type
        return None
    
    def _create_shell_request(self, step: Step) -> BaseRequest:
        """Create shell request with environment awareness"""
        from src.operations.shell.shell_request import ShellRequest
        
        # Format command with context
        cmd = self._format_step_values(step.cmd)
        
        # Get environment-specific settings
        timeout = self.env_manager.get_timeout()
        cwd = self._format_value(step.cwd) if step.cwd else self.env_manager.get_working_directory()
        
        return ShellRequest(
            cmd=cmd,
            timeout=timeout,
            cwd=cwd,
            env=step.env,
            shell=self.env_manager.get_shell()
        )
    
    def _create_file_request(self, step: Step) -> BaseRequest:
        """Create file request"""
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        
        # Determine file operation type
        if len(step.cmd) == 1:
            # Single path operations (mkdir, exists, etc.)
            path = self._format_value(step.cmd[0])
            
            # Infer operation from step metadata or default
            op_type = FileOpType.MKDIR  # Default, should be specified in step
            
            return FileRequest(
                op_type=op_type,
                path=path
            )
        elif len(step.cmd) == 2:
            # Two path operations (copy, move)
            src = self._format_value(step.cmd[0])
            dst = self._format_value(step.cmd[1])
            
            return FileRequest(
                op_type=FileOpType.COPY,
                path=src,
                dst_path=dst
            )
        
        return None
    
    def _create_copy_request(self, step: Step) -> BaseRequest:
        """Create copy request (file operation)"""
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        
        if len(step.cmd) >= 2:
            src = self._format_value(step.cmd[0])
            dst = self._format_value(step.cmd[1])
            
            return FileRequest(
                op_type=FileOpType.COPY,
                path=src,
                dst_path=dst
            )
        
        return None
    
    def _create_docker_request(self, step: Step) -> BaseRequest:
        """Create docker request"""
        # Docker requests are handled specially
        # This is a simplified version
        from src.operations.docker.docker_request import DockerRequest
        
        # Parse docker command
        # TODO: Implement proper docker command parsing
        return None
    
    def _create_python_request(self, step: Step) -> BaseRequest:
        """Create python execution request"""
        from src.operations.python.python_request import PythonRequest
        
        # Join command lines
        code = '\\n'.join(self._format_step_values(step.cmd))
        
        return PythonRequest(
            code=code,
            timeout=self.env_manager.get_timeout()
        )
    
    def _create_test_request(self, step: Step) -> BaseRequest:
        """Create test execution request"""
        # Test requests need special handling
        # For now, treat as shell request
        return self._create_shell_request(step)
    
    def _create_oj_request(self, step: Step) -> BaseRequest:
        """Create online judge tool request"""
        # OJ requests typically run in special environment
        # For now, treat as shell request
        return self._create_shell_request(step)
    
    def _format_value(self, value: str) -> str:
        """Format a single value with context"""
        if hasattr(self.context, 'format_string'):
            return self.context.format_string(value)
        return value
    
    def _format_step_values(self, values: List[str]) -> List[str]:
        """Format a list of values with context"""
        return [self._format_value(v) for v in values]