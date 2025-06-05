"""
Docker-specific error handler implementation
"""
import time
import logging
from typing import Dict, List, Any

from ...core.interfaces import ErrorHandler
from ...core.models import (
    PreparationError, ErrorSeverity, ErrorCategory
)


class DockerErrorHandler(ErrorHandler):
    """Docker-specific implementation of ErrorHandler"""
    
    def __init__(self, context=None, max_attempts: int = 3, base_delay: float = 1.0):
        """Initialize Docker error handler
        
        Args:
            context: Execution context with env.json settings
            max_attempts: Maximum retry attempts (fallback)
            base_delay: Base delay between retries in seconds (fallback)
        """
        self.context = context
        self.max_attempts = context.get_max_retry_attempts() if context else max_attempts
        self.base_delay = context.settings.base_delay_seconds if context else base_delay
        self.error_history: List[PreparationError] = []
        self.logger = logging.getLogger(__name__)
    
    def handle_error(self, error: Exception, context: Dict[str, Any]) -> PreparationError:
        """Classify and handle a Docker-related preparation error
        
        Args:
            error: The exception that occurred
            context: Context information about the operation
            
        Returns:
            PreparationError object with classification and suggestions
        """
        prep_error = self._classify_docker_error(error, context)
        self.error_history.append(prep_error)
        self.logger.error(f"Docker preparation error: {prep_error.message}", extra={
            "category": prep_error.category.value,
            "severity": prep_error.severity.value,
            "context": context
        })
        return prep_error
    
    def should_retry(self, error: PreparationError, attempt_count: int) -> bool:
        """Determine if a Docker operation should be retried
        
        Args:
            error: The preparation error
            attempt_count: Current attempt number (1-based)
            
        Returns:
            True if retry should be attempted
        """
        if attempt_count >= self.max_attempts:
            return False
        
        if not error.retry_possible:
            return False
        
        # Don't retry critical errors
        if error.severity == ErrorSeverity.CRITICAL:
            return False
        
        # Docker-specific retry logic
        retryable_categories = [
            ErrorCategory.DOCKER_DAEMON,
            ErrorCategory.DOCKER_CONTAINER,
            ErrorCategory.NETWORK
        ]
        
        return error.category in retryable_categories
    
    def get_retry_delay(self, attempt_count: int) -> float:
        """Calculate delay before retry using env.json settings
        
        Args:
            attempt_count: Current attempt number (1-based)
            
        Returns:
            Delay in seconds
        """
        if self.context:
            return self.context.get_retry_delay(attempt_count)
        else:
            # Fallback calculation
            delay = self.base_delay * (2 ** (attempt_count - 1))
            return min(delay, 30.0)
    
    def _classify_docker_error(self, error: Exception, context: Dict[str, Any]) -> PreparationError:
        """Classify a Docker-related error using env.json error patterns
        
        Args:
            error: The exception that occurred
            context: Context information
            
        Returns:
            Classified PreparationError
        """
        error_str = str(error).lower()
        
        # Use env.json error patterns if available
        if self.context:
            # Docker daemon errors from env.json
            daemon_patterns = self.context.get_error_patterns("daemon_connection")
            if daemon_patterns and any(phrase in error_str for phrase in daemon_patterns):
                return PreparationError(
                    category=ErrorCategory.DOCKER_DAEMON,
                    severity=ErrorSeverity.CRITICAL,
                    message="Docker daemon is not accessible",
                    details={"original_error": str(error)},
                    retry_possible=True,
                    suggested_action="Ensure Docker daemon is running and accessible",
                    context=context
                )
            
            # Docker image errors from env.json
            image_patterns = self.context.get_error_patterns("image_not_found")
            if image_patterns and any(phrase in error_str for phrase in image_patterns):
                return PreparationError(
                    category=ErrorCategory.DOCKER_IMAGE,
                    severity=ErrorSeverity.HIGH,
                    message="Docker image not available",
                    details={"original_error": str(error)},
                    retry_possible=True,
                    suggested_action="Check image name or build the image locally",
                    context=context
                )
            
            # Container conflict errors from env.json
            container_patterns = self.context.get_error_patterns("container_conflict")
            if container_patterns and any(phrase in error_str for phrase in container_patterns):
                return PreparationError(
                    category=ErrorCategory.DOCKER_CONTAINER,
                    severity=ErrorSeverity.MEDIUM,
                    message="Docker container conflict",
                    details={"original_error": str(error)},
                    retry_possible=True,
                    suggested_action="Remove conflicting container or use different name",
                    context=context
                )
            
            # Build errors from env.json
            build_patterns = self.context.get_error_patterns("build_error")
            if build_patterns and any(phrase in error_str for phrase in build_patterns):
                return PreparationError(
                    category=ErrorCategory.DOCKER_IMAGE,
                    severity=ErrorSeverity.HIGH,
                    message="Docker build failed",
                    details={"original_error": str(error)},
                    retry_possible=False,
                    suggested_action="Check Dockerfile syntax and build context",
                    context=context
                )
            
            # Network errors from env.json
            network_patterns = self.context.get_error_patterns("network_error")
            if network_patterns and any(phrase in error_str for phrase in network_patterns):
                return PreparationError(
                    category=ErrorCategory.NETWORK,
                    severity=ErrorSeverity.MEDIUM,
                    message="Network operation failed",
                    details={"original_error": str(error)},
                    retry_possible=True,
                    suggested_action="Check network connectivity and Docker registry access",
                    context=context
                )
            
            # Filesystem errors from env.json
            fs_patterns = self.context.get_error_patterns("filesystem_error")
            if fs_patterns and any(phrase in error_str for phrase in fs_patterns):
                return PreparationError(
                    category=ErrorCategory.FILESYSTEM,
                    severity=ErrorSeverity.HIGH,
                    message="Filesystem operation failed",
                    details={"original_error": str(error)},
                    retry_possible=False,
                    suggested_action="Check file permissions and disk space",
                    context=context
                )
            
            # Resource errors from env.json
            resource_patterns = self.context.get_error_patterns("resource_error")
            if resource_patterns and any(phrase in error_str for phrase in resource_patterns):
                return PreparationError(
                    category=ErrorCategory.RESOURCE,
                    severity=ErrorSeverity.HIGH,
                    message="Resource constraint encountered",
                    details={"original_error": str(error)},
                    retry_possible=False,
                    suggested_action="Free up system resources or increase limits",
                    context=context
                )
        
        # Fallback to hardcoded patterns if env.json not available
        # Docker daemon errors (fallback)
        if any(phrase in error_str for phrase in [
            "cannot connect to the docker daemon",
            "docker daemon is not running",
            "connection refused",
            "docker.sock"
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
        
        # Docker image errors (fallback)
        if any(phrase in error_str for phrase in [
            "no such image",
            "pull access denied",
            "repository does not exist",
            "image not found",
            "manifest unknown"
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
            "conflict",
            "name is already in use"
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
        
        # Docker build errors
        if any(phrase in error_str for phrase in [
            "dockerfile",
            "build failed",
            "build context",
            "step failed"
        ]):
            return PreparationError(
                category=ErrorCategory.DOCKER_IMAGE,
                severity=ErrorSeverity.HIGH,
                message="Docker build failed",
                details={"original_error": str(error)},
                retry_possible=False,
                suggested_action="Check Dockerfile syntax and build context",
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
            "network", "timeout", "connection", "dns", "tls"
        ]):
            return PreparationError(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message="Network operation failed",
                details={"original_error": str(error)},
                retry_possible=True,
                suggested_action="Check network connectivity and Docker registry access",
                context=context
            )
        
        # Resource errors
        if any(phrase in error_str for phrase in [
            "out of memory", "resource", "quota", "limit", "no space left"
        ]):
            return PreparationError(
                category=ErrorCategory.RESOURCE,
                severity=ErrorSeverity.HIGH,
                message="Resource constraint encountered",
                details={"original_error": str(error)},
                retry_possible=False,
                suggested_action="Free up system resources or increase limits",
                context=context
            )
        
        # Generic Docker error
        return PreparationError(
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.MEDIUM,
            message=f"Docker operation failed: {str(error)}",
            details={"original_error": str(error)},
            retry_possible=True,
            suggested_action="Review Docker configuration and try again",
            context=context
        )
    
    def generate_error_report(self) -> Dict[str, Any]:
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
        
        # Generate Docker-specific recommendations
        recommendations = []
        if by_category.get("docker_daemon", 0) > 0:
            recommendations.append("Check Docker installation and daemon status with 'docker info'")
        if by_category.get("docker_image", 0) > 0:
            recommendations.append("Verify Docker image names and registry access")
        if by_category.get("docker_container", 0) > 0:
            recommendations.append("Clean up conflicting containers with 'docker container prune'")
        if by_category.get("filesystem", 0) > 0:
            recommendations.append("Check file permissions and disk space")
        if by_category.get("network", 0) > 0:
            recommendations.append("Verify network connectivity and Docker registry access")
        
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
    
    def execute_with_retry(self, task, operations) -> bool:
        """Execute a task with Docker-specific retry logic
        
        Args:
            task: Task to execute
            operations: Operations container
            
        Returns:
            True if task succeeded
        """
        attempt = 1
        
        while attempt <= self.max_attempts:
            try:
                # Execute the task
                unified_driver = operations.resolve("unified_driver")
                result = task.request_object.execute(unified_driver)
                
                if hasattr(result, 'success') and result.success:
                    self.logger.info(f"Docker task {task.task_id} succeeded on attempt {attempt}")
                    return True
                else:
                    raise Exception(f"Task execution failed: {getattr(result, 'stderr', 'Unknown error')}")
                    
            except Exception as e:
                context = {
                    "task_id": task.task_id,
                    "task_type": task.task_type,
                    "attempt": attempt,
                    "description": task.description
                }
                
                prep_error = self.handle_error(e, context)
                
                if attempt < self.max_attempts and self.should_retry(prep_error, attempt):
                    delay = self.get_retry_delay(attempt)
                    self.logger.warning(f"Docker task {task.task_id} failed on attempt {attempt}, retrying in {delay}s")
                    time.sleep(delay)
                    attempt += 1
                else:
                    self.logger.error(f"Docker task {task.task_id} failed permanently after {attempt} attempts")
                    return False
        
        return False