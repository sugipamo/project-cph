"""Standardized error codes for structured error handling."""
from enum import Enum


class ErrorCode(Enum):
    """Standard error codes for the application."""

    # File Operation Errors
    FILE_NOT_FOUND = "FILE_NOT_FOUND"
    FILE_PERMISSION_DENIED = "FILE_PERMISSION_DENIED"
    FILE_IO_ERROR = "FILE_IO_ERROR"
    DIRECTORY_NOT_FOUND = "DIRECTORY_NOT_FOUND"
    INVALID_FILE_PATH = "INVALID_FILE_PATH"

    # Shell Operation Errors
    COMMAND_NOT_FOUND = "COMMAND_NOT_FOUND"
    COMMAND_TIMEOUT = "COMMAND_TIMEOUT"
    COMMAND_PERMISSION_DENIED = "COMMAND_PERMISSION_DENIED"
    SHELL_EXECUTION_ERROR = "SHELL_EXECUTION_ERROR"
    INVALID_COMMAND = "INVALID_COMMAND"

    # Docker Operation Errors
    DOCKER_NOT_AVAILABLE = "DOCKER_NOT_AVAILABLE"
    CONTAINER_NOT_FOUND = "CONTAINER_NOT_FOUND"
    IMAGE_NOT_FOUND = "IMAGE_NOT_FOUND"
    DOCKER_PERMISSION_DENIED = "DOCKER_PERMISSION_DENIED"
    CONTAINER_ALREADY_RUNNING = "CONTAINER_ALREADY_RUNNING"
    CONTAINER_START_FAILED = "CONTAINER_START_FAILED"
    DOCKERFILE_BUILD_FAILED = "DOCKERFILE_BUILD_FAILED"

    # Python Operation Errors
    PYTHON_NOT_FOUND = "PYTHON_NOT_FOUND"
    PYTHON_SYNTAX_ERROR = "PYTHON_SYNTAX_ERROR"
    PYTHON_RUNTIME_ERROR = "PYTHON_RUNTIME_ERROR"
    PYTHON_MODULE_NOT_FOUND = "PYTHON_MODULE_NOT_FOUND"

    # Configuration Errors
    CONFIG_NOT_FOUND = "CONFIG_NOT_FOUND"
    CONFIG_PARSE_ERROR = "CONFIG_PARSE_ERROR"
    INVALID_CONFIG_VALUE = "INVALID_CONFIG_VALUE"

    # Workflow Errors
    WORKFLOW_DEPENDENCY_FAILED = "WORKFLOW_DEPENDENCY_FAILED"
    WORKFLOW_STEP_FAILED = "WORKFLOW_STEP_FAILED"
    WORKFLOW_TIMEOUT = "WORKFLOW_TIMEOUT"

    # Network Errors
    NETWORK_TIMEOUT = "NETWORK_TIMEOUT"
    NETWORK_CONNECTION_FAILED = "NETWORK_CONNECTION_FAILED"

    # Generic Errors
    UNKNOWN_ERROR = "UNKNOWN_ERROR"
    INTERNAL_ERROR = "INTERNAL_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"


class ErrorSuggestion:
    """Provides actionable suggestions for error recovery."""

    @staticmethod
    def get_suggestion(error_code: ErrorCode) -> str:
        """Get actionable suggestion for an error code."""
        suggestions = {
            ErrorCode.FILE_NOT_FOUND: "Check if the file path exists and is accessible",
            ErrorCode.FILE_PERMISSION_DENIED: "Verify file permissions or run with appropriate privileges",
            ErrorCode.COMMAND_NOT_FOUND: "Ensure the command is installed and in PATH",
            ErrorCode.COMMAND_TIMEOUT: "Consider increasing timeout or checking system resources",
            ErrorCode.DOCKER_NOT_AVAILABLE: "Start Docker service or check Docker installation",
            ErrorCode.CONTAINER_NOT_FOUND: "Verify container name or create the container first",
            ErrorCode.IMAGE_NOT_FOUND: "Pull the image with 'docker pull <image>' or check image name",
            ErrorCode.PYTHON_NOT_FOUND: "Install Python or check Python installation path",
            ErrorCode.CONFIG_NOT_FOUND: "Create configuration file or check file path",
            ErrorCode.CONFIG_PARSE_ERROR: "Check configuration file syntax",
            ErrorCode.NETWORK_TIMEOUT: "Check network connection and retry",
        }
        return suggestions.get(error_code, "Contact support for assistance")

    @staticmethod
    def get_recovery_actions(error_code: ErrorCode) -> list[str]:
        """Get specific recovery actions for an error code."""
        recovery_actions = {
            ErrorCode.FILE_NOT_FOUND: [
                "Verify the file path is correct",
                "Check if the file was moved or deleted",
                "Ensure you have read permissions for the directory"
            ],
            ErrorCode.COMMAND_NOT_FOUND: [
                "Install the missing command",
                "Add the command location to PATH",
                "Use absolute path to the command"
            ],
            ErrorCode.DOCKER_NOT_AVAILABLE: [
                "Start Docker Desktop or Docker daemon",
                "Check Docker service status: systemctl status docker",
                "Verify Docker installation"
            ],
            ErrorCode.CONTAINER_NOT_FOUND: [
                "List available containers: docker ps -a",
                "Create the container if it doesn't exist",
                "Check container name spelling"
            ],
            ErrorCode.NETWORK_TIMEOUT: [
                "Check internet connection",
                "Verify firewall settings",
                "Try again with a longer timeout"
            ]
        }
        return recovery_actions.get(error_code, ["Contact support for assistance"])


def classify_error(exception: Exception, context: str = "") -> ErrorCode:
    """Classify an exception into a standard error code."""
    error_message = str(exception).lower()

    # File-related errors
    file_error = _classify_file_errors(error_message, context)
    if file_error:
        return file_error

    # Command-related errors
    command_error = _classify_command_errors(error_message, context)
    if command_error:
        return command_error

    # Docker-related errors
    docker_error = _classify_docker_errors(error_message)
    if docker_error:
        return docker_error

    # Python-related errors
    python_error = _classify_python_errors(exception, error_message)
    if python_error:
        return python_error

    # Configuration errors
    config_error = _classify_config_errors(error_message)
    if config_error:
        return config_error

    # Network errors
    network_error = _classify_network_errors(error_message)
    if network_error:
        return network_error

    return ErrorCode.UNKNOWN_ERROR


def _classify_file_errors(error_message: str, context: str) -> ErrorCode:
    """Classify file-related errors."""
    if "no such file or directory" in error_message or "file not found" in error_message:
        return ErrorCode.FILE_NOT_FOUND
    if "permission denied" in error_message and "file" in context.lower():
        return ErrorCode.FILE_PERMISSION_DENIED
    return None


def _classify_command_errors(error_message: str, context: str) -> ErrorCode:
    """Classify command-related errors."""
    if "command not found" in error_message or "no such file or directory" in error_message:
        return ErrorCode.COMMAND_NOT_FOUND
    if "timeout" in error_message:
        return ErrorCode.COMMAND_TIMEOUT
    if "permission denied" in error_message and "command" in context.lower():
        return ErrorCode.COMMAND_PERMISSION_DENIED
    return None


def _classify_docker_errors(error_message: str) -> ErrorCode:
    """Classify Docker-related errors."""
    if "docker" not in error_message:
        return None

    if "not found" in error_message:
        if "container" in error_message:
            return ErrorCode.CONTAINER_NOT_FOUND
        if "image" in error_message:
            return ErrorCode.IMAGE_NOT_FOUND
    if "permission denied" in error_message:
        return ErrorCode.DOCKER_PERMISSION_DENIED
    if "already running" in error_message:
        return ErrorCode.CONTAINER_ALREADY_RUNNING
    return None


def _classify_python_errors(exception: Exception, error_message: str) -> ErrorCode:
    """Classify Python-related errors."""
    if isinstance(exception, SyntaxError):
        return ErrorCode.PYTHON_SYNTAX_ERROR
    if isinstance(exception, ModuleNotFoundError):
        return ErrorCode.PYTHON_MODULE_NOT_FOUND
    if "python" in error_message and "not found" in error_message:
        return ErrorCode.PYTHON_NOT_FOUND
    return None


def _classify_config_errors(error_message: str) -> ErrorCode:
    """Classify configuration-related errors."""
    if "config" not in error_message and "configuration" not in error_message:
        return None

    if "not found" in error_message:
        return ErrorCode.CONFIG_NOT_FOUND
    if "parse" in error_message or "syntax" in error_message:
        return ErrorCode.CONFIG_PARSE_ERROR
    return None


def _classify_network_errors(error_message: str) -> ErrorCode:
    """Classify network-related errors."""
    if "timeout" in error_message and ("network" in error_message or "connection" in error_message):
        return ErrorCode.NETWORK_TIMEOUT
    if "connection" in error_message and "failed" in error_message:
        return ErrorCode.NETWORK_CONNECTION_FAILED
    return None
