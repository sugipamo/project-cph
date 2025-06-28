"""Environment manager - simplified direct implementation
"""
from typing import Any, Optional
from unittest.mock import Mock

# 互換性維持: configuration層への逆方向依存を削除、依存性注入で解決
from src.operations.interfaces.utility_interfaces import LoggerInterface
from src.operations.requests.request_factory import OperationRequestFoundation
from src.operations.results.result import OperationResult


class EnvironmentManager:
    """Simplified environment manager without strategy pattern.
    Direct implementation for basic environment management.
    """

    def __init__(self, env_type: Optional[str], config_provider, logger: LoggerInterface):
        """Initialize environment manager.

        Args:
            env_type: Environment type to use (local, docker, etc.)
            config_manager: Configuration manager instance
            logger: Logger interface for logging
        """
        self._config_provider = config_provider
        self.logger = logger
        if env_type is not None:
            self._env_type = env_type
        else:
            try:
                # Load configuration with required parameters - no defaults allowed
                self._config_manager.load_from_files(
                    system_dir="./config/system",
                    env_dir="./contest_env",
                    language="python"  # Default language for environment initialization
                )
                self._env_type = self._config_manager.resolve_config(['env_default', 'env_type'], str)
            except KeyError as e:
                raise ValueError("Environment type not provided and no default env_type found in configuration") from e

    def prepare_environment(self, context: Any) -> OperationResult:
        """Prepare the environment for execution.

        Args:
            context: Execution context

        Returns:
            OperationResult indicating success/failure
        """
        return self._create_success_result(
            operation="prepare_environment",
            message=f"Environment {self._env_type} prepared"
        )

    def cleanup_environment(self, context: Any) -> OperationResult:
        """Clean up the environment after execution.

        Args:
            context: Execution context

        Returns:
            OperationResult indicating success/failure
        """
        return self._create_success_result(
            operation="cleanup_environment",
            message=f"Environment {self._env_type} cleaned up"
        )

    def _create_success_result(self, operation: str, message: str) -> OperationResult:
        """Create a successful OperationResult."""
        mock_request = Mock()
        mock_request.operation_type = operation
        mock_exception = Exception("No error - successful operation")
        return OperationResult(
            success=True,
            returncode=0,
            stdout=None,
            stderr=None,
            content=None,
            exists=None,
            path=None,
            op=operation,
            cmd=None,
            request=mock_request,
            start_time=None,
            end_time=None,
            error_message=message,
            exception=mock_exception,
            metadata={},
            skipped=False
        )

    def execute_request(self, request: OperationRequestFoundation, driver: Any) -> OperationResult:
        """Execute a request using the appropriate environment.

        Args:
            request: The request to execute
            driver: The driver to use

        Returns:
            OperationResult with execution details
        """
        # Direct execution without strategy pattern
        return request.execute_operation(driver, self.logger)

    def should_force_local(self, step_config: dict[str, Any]) -> bool:
        """Check if a step should be forced to run locally.

        Args:
            step_config: Step configuration

        Returns:
            True if step should run locally
        """
        # Check if force_env_type is set to 'local'
        if 'force_env_type' in step_config:
            force_env_type = step_config['force_env_type']
            if force_env_type == 'local':
                return True

        # Check force_local for backwards compatibility
        # 互換性維持のため force_local フィールドもサポート
        if 'force_local' in step_config:
            force_local_value = step_config['force_local']
            if force_local_value:
                return True

        # Check if current environment is local
        return self._env_type == 'local'

    def get_working_directory(self) -> str:
        """Get the working directory for this environment"""
        return "."

    def get_timeout(self) -> int:
        """Get the default timeout for this environment"""
        return 300  # 5 minutes default

    def get_shell(self) -> str:
        """Get the default shell for this environment"""
        return "bash"

    def get_workspace_root(self) -> str:
        """Get the workspace root directory path"""
        return "./workspace"

    @classmethod
    def from_context(cls, context: Any, config_provider, logger: LoggerInterface) -> 'EnvironmentManager':
        """Create an EnvironmentManager from an execution context.

        Args:
            context: Execution context with env_type
            config_manager: Configuration manager instance
            logger: Logger interface for logging

        Returns:
            EnvironmentManager instance
        """
        # 互換性維持: hasattr()によるgetattr()デフォルト値の代替
        env_type = context.env_type if hasattr(context, 'env_type') else None
        return cls(env_type, config_provider, logger)

    def switch_environment(self, env_type: str):
        """Switch to a different environment type.

        Args:
            env_type: New environment type
        """
        self._env_type = env_type
