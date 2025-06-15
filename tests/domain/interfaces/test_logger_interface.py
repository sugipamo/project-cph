"""Tests for logger interface."""
from unittest.mock import Mock

from src.domain.interfaces.logger_interface import LoggerInterface


class MockLogger(LoggerInterface):
    """Mock implementation for testing."""

    def __init__(self):
        self.messages = []

    def debug(self, message: str, *args, **kwargs) -> None:
        self.messages.append(("debug", message, args, kwargs))

    def info(self, message: str, *args, **kwargs) -> None:
        self.messages.append(("info", message, args, kwargs))

    def warning(self, message: str, *args, **kwargs) -> None:
        self.messages.append(("warning", message, args, kwargs))

    def error(self, message: str, *args, **kwargs) -> None:
        self.messages.append(("error", message, args, kwargs))

    def critical(self, message: str, *args, **kwargs) -> None:
        self.messages.append(("critical", message, args, kwargs))


class TestLoggerInterface:
    """Test logger interface implementation."""

    def test_debug_logging(self):
        logger = MockLogger()
        logger.debug("Debug message")
        assert len(logger.messages) == 1
        assert logger.messages[0][0] == "debug"
        assert logger.messages[0][1] == "Debug message"

    def test_info_logging(self):
        logger = MockLogger()
        logger.info("Info message")
        assert len(logger.messages) == 1
        assert logger.messages[0][0] == "info"
        assert logger.messages[0][1] == "Info message"

    def test_warning_logging(self):
        logger = MockLogger()
        logger.warning("Warning message")
        assert len(logger.messages) == 1
        assert logger.messages[0][0] == "warning"
        assert logger.messages[0][1] == "Warning message"

    def test_error_logging(self):
        logger = MockLogger()
        logger.error("Error message")
        assert len(logger.messages) == 1
        assert logger.messages[0][0] == "error"
        assert logger.messages[0][1] == "Error message"

    def test_critical_logging(self):
        logger = MockLogger()
        logger.critical("Critical message")
        assert len(logger.messages) == 1
        assert logger.messages[0][0] == "critical"
        assert logger.messages[0][1] == "Critical message"

    def test_logging_with_args(self):
        logger = MockLogger()
        logger.info("Message with %s", "args")
        assert len(logger.messages) == 1
        assert logger.messages[0][1] == "Message with %s"
        assert logger.messages[0][2] == ("args",)

    def test_logging_with_kwargs(self):
        logger = MockLogger()
        logger.info("Message", extra={"key": "value"})
        assert len(logger.messages) == 1
        assert logger.messages[0][1] == "Message"
        assert logger.messages[0][3] == {"extra": {"key": "value"}}

    def test_multiple_log_levels(self):
        logger = MockLogger()
        logger.debug("Debug")
        logger.info("Info")
        logger.warning("Warning")
        logger.error("Error")
        logger.critical("Critical")

        assert len(logger.messages) == 5
        levels = [msg[0] for msg in logger.messages]
        assert levels == ["debug", "info", "warning", "error", "critical"]
