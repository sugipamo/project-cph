"""Robust error handling for preparation and fitting operations
"""
import logging
import time
from dataclasses import dataclass
from enum import Enum
from typing import Any, Optional


class ErrorSeverity(Enum):
    """Error severity levels for preparation failures"""
    CRITICAL = "critical"      # Prevents any execution
    HIGH = "high"             # Prevents current operation but alternatives may exist
    MEDIUM = "medium"         # May affect performance or functionality
    LOW = "low"              # Minor issues that don't block execution


class ErrorCategory(Enum):
    """Categories of preparation errors"""
    DOCKER_DAEMON = "docker_daemon"
    DOCKER_IMAGE = "docker_image"
    DOCKER_CONTAINER = "docker_container"
    FILESYSTEM = "filesystem"
    NETWORK = "network"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    DEPENDENCY = "dependency"


@dataclass
class PreparationError:
    """Represents a preparation error with context"""
    category: ErrorCategory
    severity: ErrorSeverity
    message: str
    details: dict[str, Any]
    retry_possible: bool = False
    suggested_action: Optional[str] = None
    context: Optional[dict[str, Any]] = None


@dataclass
class RetryStrategy:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 30.0
    exponential_backoff: bool = True
    retry_on_categories: list[ErrorCategory] = None


class PreparationErrorHandler:
    """Handles errors during preparation with retry and recovery strategies"""

    def __init__(self, retry_strategy: Optional[RetryStrategy] = None):
        """Initialize error handler with retry configuration

        Args:
            retry_strategy: Configuration for retry behavior
        """
        self.retry_strategy = retry_strategy or RetryStrategy()
        self.error_history: list[PreparationError] = []
        self.logger = logging.getLogger(__name__)

    def handle_error(self, error: Exception, context: dict[str, Any]) -> PreparationError:
        """Classify and handle a preparation error

        Args:
            error: The exception that occurred
            context: Context information about the operation

        Returns:
            PreparationError object with classification and suggestions
        """
        prep_error = self._classify_error(error, context)
        self.error_history.append(prep_error)
        self.logger.error(f"Preparation error: {prep_error.message}", extra={
            "category": prep_error.category.value,
            "severity": prep_error.severity.value,
            "context": context
        })
        return prep_error

    def should_retry(self, error: PreparationError, attempt_count: int) -> bool:
        """Determine if an operation should be retried

        Args:
            error: The preparation error
            attempt_count: Current attempt number (1-based)

        Returns:
            True if retry should be attempted
        """
        if attempt_count >= self.retry_strategy.max_attempts:
            return False

        if not error.retry_possible:
            return False

        if self.retry_strategy.retry_on_categories:
            if error.category not in self.retry_strategy.retry_on_categories:
                return False

        # Don't retry critical errors
        return error.severity != ErrorSeverity.CRITICAL

    def get_retry_delay(self, attempt_count: int) -> float:
        """Calculate delay before retry

        Args:
            attempt_count: Current attempt number (1-based)

        Returns:
            Delay in seconds
        """
        if self.retry_strategy.exponential_backoff:
            delay = self.retry_strategy.base_delay * (2 ** (attempt_count - 1))
        else:
            delay = self.retry_strategy.base_delay

        return min(delay, self.retry_strategy.max_delay)

    def _classify_error(self, error: Exception, context: dict[str, Any]) -> PreparationError:
        """Classify an error and provide appropriate metadata

        Args:
            error: The exception that occurred
            context: Context information

        Returns:
            Classified PreparationError
        """
        error_str = str(error).lower()

        # Docker daemon errors
        if any(phrase in error_str for phrase in [
            "cannot connect to the docker daemon",
            "docker daemon is not running",
            "connection refused"
        ]):
            return PreparationError(
                category=ErrorCategory.DOCKER_DAEMON,
                severity=ErrorSeverity.CRITICAL,
                message="Docker daemon is not accessible",
                details={"original_error": str(error)},
                retry_possible=True,
                suggested_action="Ensure Docker daemon is running and accessible",
                context=context
            )

        # Docker image errors
        if any(phrase in error_str for phrase in [
            "no such image",
            "pull access denied",
            "repository does not exist",
            "image not found"
        ]):
            return PreparationError(
                category=ErrorCategory.DOCKER_IMAGE,
                severity=ErrorSeverity.HIGH,
                message="Docker image not available",
                details={"original_error": str(error)},
                retry_possible=True,
                suggested_action="Check image name or build the image locally",
                context=context
            )

        # Docker container errors
        if any(phrase in error_str for phrase in [
            "container already exists",
            "container is running",
            "container not found",
            "conflict"
        ]):
            return PreparationError(
                category=ErrorCategory.DOCKER_CONTAINER,
                severity=ErrorSeverity.MEDIUM,
                message="Docker container conflict",
                details={"original_error": str(error)},
                retry_possible=True,
                suggested_action="Remove conflicting container or use different name",
                context=context
            )

        # Filesystem errors
        if any(phrase in error_str for phrase in [
            "permission denied",
            "no such file or directory",
            "directory not empty",
            "disk space"
        ]):
            return PreparationError(
                category=ErrorCategory.FILESYSTEM,
                severity=ErrorSeverity.HIGH,
                message="Filesystem operation failed",
                details={"original_error": str(error)},
                retry_possible=False,
                suggested_action="Check file permissions and disk space",
                context=context
            )

        # Network errors
        if any(phrase in error_str for phrase in [
            "network", "timeout", "connection", "dns"
        ]):
            return PreparationError(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message="Network operation failed",
                details={"original_error": str(error)},
                retry_possible=True,
                suggested_action="Check network connectivity",
                context=context
            )

        # Resource errors
        if any(phrase in error_str for phrase in [
            "out of memory", "resource", "quota", "limit"
        ]):
            return PreparationError(
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.HIGH,
                message="Resource constraint encountered",
                details={"original_error": str(error)},
                retry_possible=False,
                suggested_action="Free up system resources",
                context=context
            )

        # Generic error
        return PreparationError(
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            message=str(error),
            details={"original_error": str(error)},
            retry_possible=True,
            suggested_action="Review configuration and try again",
            context=context
        )

    def generate_error_report(self) -> dict[str, Any]:
        """Generate a comprehensive error report

        Returns:
            Dictionary with error analysis and recommendations
        """
        if not self.error_history:
            return {"status": "no_errors", "errors": []}

        # Categorize errors
        by_category = {}
        by_severity = {}

        for error in self.error_history:
            cat = error.category.value
            sev = error.severity.value

            by_category[cat] = by_category.get(cat, 0) + 1
            by_severity[sev] = by_severity.get(sev, 0) + 1

        # Generate recommendations
        recommendations = []
        if by_category.get("docker_daemon", 0) > 0:
            recommendations.append("Check Docker installation and daemon status")
        if by_category.get("docker_image", 0) > 0:
            recommendations.append("Verify Docker image names and availability")
        if by_category.get("filesystem", 0) > 0:
            recommendations.append("Check file permissions and disk space")

        return {
            "status": "errors_found",
            "total_errors": len(self.error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recommendations": recommendations,
            "errors": [
                {
                    "category": e.category.value,
                    "severity": e.severity.value,
                    "message": e.message,
                    "suggested_action": e.suggested_action
                }
                for e in self.error_history[-10:]  # Last 10 errors
            ]
        }


class RobustPreparationExecutor:
    """Preparation executor with robust error handling and retry logic"""

    def __init__(self, base_executor, error_handler: Optional[PreparationErrorHandler] = None):
        """Initialize robust executor

        Args:
            base_executor: The base preparation executor
            error_handler: Error handler instance
        """
        self.base_executor = base_executor
        self.error_handler = error_handler or PreparationErrorHandler()
        self.logger = logging.getLogger(__name__)

    def execute_with_retry(self, preparation_tasks: list, max_retries: int = 3) -> tuple[bool, list, list]:
        """Execute preparation tasks with retry logic

        Args:
            preparation_tasks: List of preparation tasks to execute
            max_retries: Maximum number of retry attempts

        Returns:
            Tuple of (success, successful_tasks, failed_tasks)
        """
        successful_tasks = []
        failed_tasks = []

        for task in preparation_tasks:
            success = self._execute_task_with_retry(task, max_retries)
            if success:
                successful_tasks.append(task)
            else:
                failed_tasks.append(task)

        return len(failed_tasks) == 0, successful_tasks, failed_tasks

    def _execute_task_with_retry(self, task, max_retries: int) -> bool:
        """Execute a single task with retry logic

        Args:
            task: Preparation task to execute
            max_retries: Maximum retry attempts

        Returns:
            True if task succeeded
        """
        attempt = 1

        while attempt <= max_retries:
            try:
                # Execute the task
                result = task.request_object.execute(self.base_executor.operations.resolve("unified_driver"))

                if hasattr(result, 'success') and result.success:
                    self.logger.info(f"Task {task.task_id} succeeded on attempt {attempt}")
                    return True
                raise Exception(f"Task execution failed: {getattr(result, 'stderr', 'Unknown error')}")

            except Exception as e:
                context = {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "attempt": attempt,
                    "description": task.description
                }

                prep_error = self.error_handler.handle_error(e, context)

                if attempt < max_retries and self.error_handler.should_retry(prep_error, attempt):
                    delay = self.error_handler.get_retry_delay(attempt)
                    self.logger.warning(f"Task {task.task_id} failed on attempt {attempt}, retrying in {delay}s")
                    time.sleep(delay)
                    attempt += 1
                else:
                    self.logger.error(f"Task {task.task_id} failed permanently after {attempt} attempts")
                    return False

        return False
