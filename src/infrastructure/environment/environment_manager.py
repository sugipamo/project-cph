"""Environment manager - simplified direct implementation
"""
from typing import Any, Optional

from src.domain.requests.base.base_request import OperationRequestFoundation
from src.domain.results.result import OperationResult


class EnvironmentManager:
    """Simplified environment manager without strategy pattern.
    Direct implementation for basic environment management.
    """

    def __init__(self, env_type: Optional[str] = None):
        """Initialize environment manager.

        Args:
            env_type: Environment type to use (local, docker, etc.)
        """
        self._env_type = env_type or "local"

    def prepare_environment(self, context: Any) -> OperationResult:
        """Prepare the environment for execution.

        Args:
            context: Execution context

        Returns:
            OperationResult indicating success/failure
        """
        # Simple direct implementation
        return OperationResult(success=True, error_message=f"Environment {self._env_type} prepared")

    def cleanup_environment(self, context: Any) -> OperationResult:
        """Clean up the environment after execution.

        Args:
            context: Execution context

        Returns:
            OperationResult indicating success/failure
        """
        # Simple direct implementation
        return OperationResult(success=True, error_message=f"Environment {self._env_type} cleaned up")

    def execute_request(self, request: OperationRequestFoundation, driver: Any) -> OperationResult:
        """Execute a request using the appropriate environment.

        Args:
            request: The request to execute
            driver: The driver to use

        Returns:
            OperationResult with execution details
        """
        # Direct execution without strategy pattern
        return request.execute_operation(driver)

    def should_force_local(self, step_config: dict[str, Any]) -> bool:
        """Check if a step should be forced to run locally.

        Args:
            step_config: Step configuration

        Returns:
            True if step should run locally
        """
        # Check if force_env_type is set to 'local'
        force_env_type = step_config.get('force_env_type')
        if force_env_type == 'local':
            return True

        # Fall back to force_local for backwards compatibility
        return step_config.get('force_local', False) or self._env_type == 'local'

    def get_working_directory(self) -> str:
        """Get the working directory for this environment"""
        return "."

    def get_timeout(self) -> int:
        """Get the default timeout for this environment"""
        return 300  # 5 minutes default

    def get_shell(self) -> str:
        """Get the default shell for this environment"""
        return "bash"

    @classmethod
    def from_context(cls, context: Any) -> 'EnvironmentManager':
        """Create an EnvironmentManager from an execution context.

        Args:
            context: Execution context with env_type

        Returns:
            EnvironmentManager instance
        """
        env_type = getattr(context, 'env_type', None)
        return cls(env_type)

    def switch_environment(self, env_type: str):
        """Switch to a different environment type.

        Args:
            env_type: New environment type
        """
        self._env_type = env_type
