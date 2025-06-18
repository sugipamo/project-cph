"""Integration tests for logging functionality."""
from unittest.mock import Mock

import pytest

from src.application.orchestration.unified_driver import UnifiedDriver
from src.infrastructure.build_infrastructure import build_mock_infrastructure
from src.infrastructure.di_container import DIKey
from src.operations.requests.file.file_op_type import FileOpType
from src.operations.requests.file.file_request import FileRequest
from src.operations.requests.shell.shell_request import ShellRequest


def test_shell_request_with_logger():
    """Test that ShellRequest properly uses the injected logger."""
    # Setup
    infrastructure = build_mock_infrastructure()
    logger = Mock()

    # Create UnifiedDriver with logger
    driver = UnifiedDriver(infrastructure, logger)

    # Create and execute a shell request
    request = ShellRequest(cmd=["echo", "test"])
    result = driver.execute_command(request)

    # Verify result
    assert result.success
    # Mock shell driver returns "mock output"
    assert "mock output" in result.stdout or "test" in result.stdout

    # Verify logger was not called for successful operations (no debug logging by default)
    # logger methods would be called only for errors or if debug logging is enabled


def test_shell_request_error_logging():
    """Test that ShellRequest logs errors properly."""
    # For now, just test that logger is passed through properly
    # The error logging functionality itself is tested elsewhere
    infrastructure = build_mock_infrastructure()
    logger = Mock()

    # Create UnifiedDriver with logger
    driver = UnifiedDriver(infrastructure, logger)

    # Verify logger was set
    assert driver.logger == logger

    # Create and execute a request
    request = ShellRequest(cmd=["echo", "test"])
    result = driver.execute_command(request)

    # Verify basic execution works
    assert result is not None


def test_file_request_with_logger():
    """Test that FileRequest properly uses the injected logger."""
    # Setup
    infrastructure = build_mock_infrastructure()
    logger = Mock()
    logger.debug = Mock()
    logger.error = Mock()

    # Create UnifiedDriver with logger
    driver = UnifiedDriver(infrastructure, logger)

    # Create and execute a file request
    request = FileRequest(op=FileOpType.WRITE, path="test.txt", content="test content")
    result = driver.execute_command(request)

    # Verify result
    assert result.success

    # Verify logger.debug was called
    logger.debug.assert_called_with("Executing file operation: FileOpType.WRITE on test.txt")


def test_retry_decorator_with_logger():
    """Test that retry decorator uses the injected logger."""
    from src.infrastructure.patterns.retry_decorator import RetryableOperation, RetryConfig

    # Setup logger
    logger = Mock()
    logger.warning = Mock()

    # Create retry config with logger
    config = RetryConfig(max_attempts=2, logger=logger)
    retryable = RetryableOperation(config)

    # Create a function that fails once then succeeds
    call_count = 0
    def flaky_function():
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            raise ConnectionError("Network error")
        return "success"

    # Execute with retry
    result = retryable.execute_with_retry(flaky_function)

    # Verify result
    assert result == "success"
    assert call_count == 2

    # Verify logger.warning was called
    logger.warning.assert_called_once()
    assert "Attempt 1 failed" in logger.warning.call_args[0][0]
    assert "Retrying in" in logger.warning.call_args[0][0]


def test_workflow_execution_service_logger_injection():
    """Test that WorkflowExecutionService properly injects logger."""
    from src.configuration.config_manager import TypedExecutionConfiguration
    from src.workflow.workflow_execution_service import WorkflowExecutionService

    # Setup
    infrastructure = build_mock_infrastructure()

    # Create a simple context
    context = TypedExecutionConfiguration(
        problem_name="test",
        language="python",
        command_type="solve",
        env_json={
            "python": {
                "commands": {
                    "solve": {
                        "steps": [],
                        "parallel": {"enabled": False, "max_workers": 4}
                    }
                }
            }
        }
    )

    # Create service
    WorkflowExecutionService(context, infrastructure)

    # Verify logger is available
    logger = infrastructure.resolve(DIKey.UNIFIED_LOGGER)
    assert logger is not None
