"""
Unified Request Factory - Consolidates all request creation logic
"""
from abc import ABC, abstractmethod
from typing import Optional, Dict, Any, List
from src.env_core.step.step import Step, StepType
from src.domain.requests.base.base_request import BaseRequest
from src.infrastructure.environment.environment_manager import EnvironmentManager
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
        from src.domain.requests.file.file_request import FileRequest
        from src.domain.requests.file.file_op_type import FileOpType
        
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
                path=formatted_cmd[0],
                allow_failure=step.allow_failure,
                name=f"{step.type.value}_{formatted_cmd[0]}"
            )
        elif len(formatted_cmd) == 2:
            # Two path operations (copy, move)
            return FileRequest(
                op=op_type,
                path=formatted_cmd[0],
                dst_path=formatted_cmd[1],
                allow_failure=step.allow_failure,
                name=f"{step.type.value}_{formatted_cmd[0]}_to_{formatted_cmd[1]}"
            )
        
        return None
    
    def _format_step_values(self, cmd: List[str], context: Any) -> List[str]:
        """Format step command values with context variables."""
        from src.pure_functions.execution_context_formatter_pure import format_values_with_context_dict
        context_dict = context.to_dict() if hasattr(context, 'to_dict') else {}
        return format_values_with_context_dict(cmd, context_dict)


class ShellRequestStrategy(RequestCreationStrategy):
    """Strategy for creating shell command requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type == StepType.SHELL
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.domain.requests.shell.shell_request import ShellRequest
        
        # Format command with context
        formatted_cmd = self._format_step_values(step.cmd, context)
        
        return ShellRequest(
            cmd=formatted_cmd,
            cwd=getattr(step, 'cwd', None),
            allow_failure=step.allow_failure,
            show_output=step.show_output,
            name=f"shell_{' '.join(formatted_cmd[:3])}"
        )
    
    def _format_step_values(self, cmd: List[str], context: Any) -> List[str]:
        """Format step command values with context variables."""
        from src.pure_functions.execution_context_formatter_pure import format_values_with_context_dict
        context_dict = context.to_dict() if hasattr(context, 'to_dict') else {}
        return format_values_with_context_dict(cmd, context_dict)


class PythonRequestStrategy(RequestCreationStrategy):
    """Strategy for creating Python execution requests"""
    
    def can_handle(self, step_type: StepType) -> bool:
        return step_type == StepType.PYTHON
    
    def create_request(self, step: Step, context: Any, env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        from src.domain.requests.python.python_request import PythonRequest
        
        # Format command with context
        formatted_cmd = self._format_step_values(step.cmd, context)
        
        return PythonRequest(
            code_or_file=formatted_cmd,
            cwd=getattr(step, 'cwd', None),
            show_output=step.show_output,
            name=f"python_{len(formatted_cmd)}_statements"
        )
    
    def _format_step_values(self, cmd: List[str], context: Any) -> List[str]:
        """Format step command values with context variables."""
        from src.pure_functions.execution_context_formatter_pure import format_values_with_context_dict
        context_dict = context.to_dict() if hasattr(context, 'to_dict') else {}
        return format_values_with_context_dict(cmd, context_dict)


class UnifiedRequestFactory:
    """
    Unified factory for creating requests from steps.
    Uses strategy pattern to handle different step types.
    """
    
    def __init__(self):
        self._strategies: List[RequestCreationStrategy] = [
            FileRequestStrategy(),
            ShellRequestStrategy(),
            PythonRequestStrategy(),
        ]
    
    def create_requests_from_steps(self, steps: List[Step], context: Any, 
                                 env_manager: EnvironmentManager) -> List[BaseRequest]:
        """
        Create requests from a list of steps.
        
        Args:
            steps: List of steps to convert
            context: Execution context
            env_manager: Environment manager
            
        Returns:
            List of created requests
        """
        requests = []
        
        for step in steps:
            request = self.create_request_from_step(step, context, env_manager)
            if request:
                requests.append(request)
        
        return requests
    
    def create_request_from_step(self, step: Step, context: Any, 
                               env_manager: EnvironmentManager) -> Optional[BaseRequest]:
        """
        Create a single request from a step.
        
        Args:
            step: Step to convert
            context: Execution context
            env_manager: Environment manager
            
        Returns:
            Created request or None if no strategy can handle it
        """
        for strategy in self._strategies:
            if strategy.can_handle(step.type):
                return strategy.create_request(step, context, env_manager)
        
        return None
    
    def register_strategy(self, strategy: RequestCreationStrategy):
        """
        Register a new request creation strategy.
        
        Args:
            strategy: Strategy to register
        """
        self._strategies.append(strategy)


def create_composite_request(steps: List[Step], context: Any = None) -> "CompositeRequest":
    """
    Create a composite request from a list of steps.
    
    Args:
        steps: List of steps to convert to requests
        context: Execution context
        
    Returns:
        CompositeRequest containing all converted steps
    """
    from src.domain.requests.composite.composite_request import CompositeRequest
    
    factory = UnifiedRequestFactory()
    requests = []
    
    for step in steps:
        request = factory.create_request_from_step(step, context, EnvironmentManager("local"))
        if request:
            requests.append(request)
    
    return CompositeRequest(requests)


def create_request(step: Step, context: Any = None) -> Optional[BaseRequest]:
    """
    Create a single request from a step.
    
    Args:
        step: Step to convert
        context: Execution context
        
    Returns:
        Request object or None if conversion failed
    """
    factory = UnifiedRequestFactory()
    return factory.create_request_from_step(step, context, EnvironmentManager("local"))