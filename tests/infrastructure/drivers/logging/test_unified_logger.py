"""Test for unified logger functionality."""

import pytest

from src.infrastructure.config.di_config import configure_test_dependencies
from src.infrastructure.di_container import DIContainer, DIKey
from src.infrastructure.drivers.logging import LogLevel, MockOutputManager, UnifiedLogger


class TestUnifiedLogger:
    """Test unified logger implementation."""

    def setup_method(self):
        """Setup test container and logger."""
        self.container = DIContainer()
        configure_test_dependencies(self.container)
        self.logger = self.container.resolve(DIKey.UNIFIED_LOGGER)

    def test_basic_logging_methods(self):
        """Test basic logging methods work."""
        self.logger.debug("Debug message")
        self.logger.info("Info message")
        self.logger.warning("Warning message")
        self.logger.error("Error message")
        self.logger.critical("Critical message")

        # Should not raise any exceptions
        assert True

    def test_step_workflow_methods(self):
        """Test workflow-specific methods work."""
        self.logger.step_start("Test Step", type="TEST")
        self.logger.step_success("Test Step", "Success message")
        self.logger.step_failure("Test Step", "Error occurred", allow_failure=True)

        # Should not raise any exceptions
        assert True

    def test_correlation_logging(self):
        """Test correlation logging methods."""
        self.logger.log_error_with_correlation("ERR001", "TEST_ERROR", "Test error", {"key": "value"})
        self.logger.log_operation_start("OP001", "TEST_OPERATION", {"detail": "test"})
        self.logger.log_operation_end("OP001", "TEST_OPERATION", True, {"result": "success"})

        # Should not raise any exceptions
        assert True

    def test_environment_logging(self):
        """Test environment information logging."""
        env_config = {
            "enabled": True,
            "show_language_name": True,
            "show_contest_name": True,
            "show_problem_name": True,
            "show_env_type": True
        }

        self.logger.log_environment_info(
            language_name="Python",
            contest_name="Test Contest",
            problem_name="Test Problem",
            env_type="Local",
            env_logging_config=env_config
        )

        # Should not raise any exceptions
        assert True

    def test_logger_interface_compatibility(self):
        """Test LoggerInterface compatibility."""
        # Test with args formatting
        self.logger.info("Hello %s", "World")
        self.logger.error("Error: %d", 404)

        # Test with kwargs (should be ignored gracefully)
        self.logger.debug("Debug message", extra={"key": "value"})

        # Should not raise any exceptions
        assert True

