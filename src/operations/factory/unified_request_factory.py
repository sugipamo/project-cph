"""
Unified Request Factory - Consolidates all request creation logic
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from src.env_core.step.step import Step, StepType
from src.operations.base_request import BaseRequest
from src.operations.environment.environment_manager import EnvironmentManager
from src.context.commands.base_command import Command


class RequestCreationStrategy(ABC):
    """
    Abstract strategy for creating specific types of requests.
    """
    
    @abstractmethod
    def can_handle(self, step_type: StepType) -> bool:
        """
        Check if this strategy can handle the given step type.
        
        Args:
            step_type: The type of step to check
            
        Returns:
            True if this strategy can handle the step type
        """
        pass
    
    @abstractmethod
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        """
        Create a request from the given step.
        
        Args:
            step: The step to convert
            context: Execution context
            env_manager: Environment manager for strategy-based execution
            
        Returns:
            Created request or None if cannot create
        """
        pass


class FileRequestStrategy(RequestCreationStrategy):
    """Strategy for creating file operation requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type in [
            StepType.MKDIR, StepType.TOUCH, StepType.COPY, 
            StepType.MOVE, StepType.MOVETREE, StepType.REMOVE
        ]
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.file.file_request import FileRequest
        from src.operations.file.file_op_type import FileOpType
        
        # Map step type to file operation type
        op_mapping = {
            StepType.MKDIR: FileOpType.MKDIR,
            StepType.TOUCH: FileOpType.TOUCH,
            StepType.COPY: FileOpType.COPY,
            StepType.MOVE: FileOpType.MOVE,
            StepType.MOVETREE: FileOpType.COPYTREE,
            StepType.REMOVE: FileOpType.REMOVE,
        }
        
        op_type = op_mapping.get(step.type)
        if not op_type:
            return None
        
        # Format command with context
        formatted_cmd = self._format_step_values(step.cmd, context)
        
        if len(formatted_cmd) == 1:
            # Single path operations
            return FileRequest(
                op=op_type,
                path=formatted_cmd[0]
            )
        elif len(formatted_cmd) >= 2:
            # Two path operations
            return FileRequest(
                op=op_type,
                path=formatted_cmd[0],
                dst_path=formatted_cmd[1]
            )
        
        return None
    
    def _format_step_values(self, values: List[str], context: Any) -> List[str]:
        """Format step values with context"""
        if hasattr(context, 'format_string'):
            return [context.format_string(v) for v in values]
        return values


class ShellRequestStrategy(RequestCreationStrategy):
    """Strategy for creating shell execution requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type == StepType.SHELL
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.shell.shell_request import ShellRequest
        
        # Format command with context
        formatted_cmd = self._format_step_values(step.cmd, context)
        
        # Get environment-specific settings
        timeout = env_manager.get_timeout()
        cwd = self._format_value(step.cwd, context) if step.cwd else env_manager.get_working_directory()
        shell = env_manager.get_shell()
        
        return ShellRequest(
            cmd=formatted_cmd,
            timeout=timeout,
            cwd=cwd,
            env=getattr(step, 'env', None)
        )
    
    def _format_value(self, value: str, context: Any) -> str:
        """Format a single value with context"""
        if hasattr(context, 'format_string'):
            return context.format_string(value)
        return value
    
    def _format_step_values(self, values: List[str], context: Any) -> List[str]:
        """Format step values with context"""
        return [self._format_value(v, context) for v in values]


class PythonRequestStrategy(RequestCreationStrategy):
    """Strategy for creating Python execution requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type == StepType.PYTHON
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.python.python_request import PythonRequest
        
        # Format and join command lines
        formatted_cmd = self._format_step_values(step.cmd, context)
        code = '\\n'.join(formatted_cmd)
        
        return PythonRequest(
            code_or_file=code
        )
    
    def _format_step_values(self, values: List[str], context: Any) -> List[str]:
        """Format step values with context"""
        if hasattr(context, 'format_string'):
            return [context.format_string(v) for v in values]
        return values


class DockerRequestStrategy(RequestCreationStrategy):
    """Strategy for creating Docker operation requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type in [StepType.DOCKER_RUN, StepType.DOCKER_EXEC, StepType.DOCKER_CP]
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.operations.docker.docker_request import DockerRequest, DockerOpType
        
        # Parse docker command
        if not step.cmd:
            return None
        
        docker_cmd = step.cmd[0].lower()
        
        # Map docker commands to operations
        op_mapping = {
            'run': DockerOpType.RUN,
            'exec': DockerOpType.EXEC,
            'cp': DockerOpType.CP,
            'build': DockerOpType.BUILD,
        }
        
        op_type = op_mapping.get(docker_cmd)
        if not op_type:
            return None
        
        # Extract container name and options
        container_name = step.cmd[1] if len(step.cmd) > 1 else "default"
        options = {}
        
        if len(step.cmd) > 2:
            options['args'] = step.cmd[2:]
        
        return DockerRequest(
            op=op_type,
            container=container_name,
            options=options
        )


class ComplexRequestStrategy(RequestCreationStrategy):
    """Strategy for creating complex requests (TEST, BUILD, OJ)"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type in [StepType.TEST, StepType.BUILD, StepType.OJ]
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        # For complex requests like TEST, BUILD, OJ, we need specific implementations
        # This is a placeholder - implement as needed for specific step types
        return None


class UnifiedRequestFactory:
    """
    Unified factory that consolidates all request creation logic.
    Uses strategy pattern to handle different request types.
    """
    
    def __init__(self):
        self._strategies: List[RequestCreationStrategy] = []
        self._initialize_strategies()
    
    def _initialize_strategies(self):
        """Initialize all request creation strategies"""
        self._strategies = [
            FileRequestStrategy(),
            ShellRequestStrategy(),
            PythonRequestStrategy(),
            DockerRequestStrategy(),
            ComplexRequestStrategy(),  # Keep last as fallback
        ]
    
    def create_request(self, step: Step, context: Any = None, env_manager: EnvironmentManager = None) -> Optional[BaseRequest]:
        """
        Create a request from a step using appropriate strategy.
        
        Args:
            step: The step to convert to a request
            context: Execution context for formatting
            env_manager: Environment manager for environment-specific logic
            
        Returns:
            Created request or None if no strategy can handle the step
        """
        # Create environment manager if not provided
        if env_manager is None:
            env_manager = EnvironmentManager.from_context(context) if context else EnvironmentManager()
        
        # Check if step should be forced to local
        if env_manager.should_force_local(step.__dict__):
            # Temporarily switch to local strategy
            original_env = env_manager._env_type
            env_manager.switch_strategy('local')
            request = self._create_request_with_strategies(step, context, env_manager)
            if original_env:
                env_manager.switch_strategy(original_env)
            return request
        
        return self._create_request_with_strategies(step, context, env_manager)
    
    def _create_request_with_strategies(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        """Create request using registered strategies"""
        for strategy in self._strategies:
            if strategy.can_handle(step.type):
                request = strategy.create_request(step, context, env_manager)
                if request:
                    return request
        
        return None
    
    def register_strategy(self, strategy: RequestCreationStrategy):
        """
        Register a new request creation strategy.
        
        Args:
            strategy: The strategy to register
        """
        self._strategies.append(strategy)
    
    def create_requests_from_steps(self, steps: List[Step], context: Any = None) -> List[BaseRequest]:
        """
        Create multiple requests from a list of steps.
        
        Args:
            steps: List of steps to convert
            context: Execution context
            
        Returns:
            List of created requests (skips steps that cannot be converted)
        """
        requests = []
        env_manager = EnvironmentManager.from_context(context) if context else EnvironmentManager()
        
        for step in steps:
            request = self.create_request(step, context, env_manager)
            if request:
                requests.append(request)
        
        return requests
    
    def create_composite_request(self, steps: List[Step], context: Any = None, operations = None):
        """
        Create a composite request from a list of steps.
        
        Args:
            steps: List of steps to convert
            context: Execution context
            operations: DI container for driver binding
            
        Returns:
            CompositeRequest containing all converted steps
        """
        from src.operations.composite.composite_request import CompositeRequest
        from src.operations.composite.driver_bound_request import DriverBoundRequest
        from src.operations.file.file_request import FileRequest
        
        requests = self.create_requests_from_steps(steps, context)
        
        # Bind drivers if operations container is provided
        if operations:
            bound_requests = []
            for request in requests:
                if isinstance(request, FileRequest):
                    file_driver = operations.resolve('file_driver')
                    request = DriverBoundRequest(request, file_driver)
                bound_requests.append(request)
            requests = bound_requests
        
        return CompositeRequest.make_composite_request(requests)


# Global unified factory instance
_unified_factory = UnifiedRequestFactory()


def create_request(step: Step, context: Any = None, env_manager: EnvironmentManager = None) -> Optional[BaseRequest]:
    """Create a request using the global unified factory"""
    return _unified_factory.create_request(step, context, env_manager)


def create_requests_from_steps(steps: List[Step], context: Any = None) -> List[BaseRequest]:
    """Create multiple requests using the global unified factory"""
    return _unified_factory.create_requests_from_steps(steps, context)


def create_composite_request(steps: List[Step], context: Any = None, operations = None):
    """Create a composite request using the global unified factory"""
    return _unified_factory.create_composite_request(steps, context, operations)


def register_strategy(strategy: RequestCreationStrategy):
    """Register a strategy in the global unified factory"""
    _unified_factory.register_strategy(strategy)