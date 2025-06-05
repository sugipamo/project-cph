"""
Comprehensive tests for PreparationErrorHandler to improve coverage
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
import time
import logging
from dataclasses import dataclass
from typing import Dict, List, Any

from src.env_integration.fitting.preparation_error_handler import (
    PreparationErrorHandler, RobustPreparationExecutor, PreparationError,
    RetryStrategy, ErrorSeverity, ErrorCategory
)



class TestPreparationError:
    """Tests for PreparationError dataclass"""
    
    
    def test_preparation_error_creation_full(self):
        """Test creating PreparationError with all parameters"""
        context = {"operation": "test"}
        error = PreparationError(
            category=ErrorCategory.DOCKER_IMAGE,
            severity=ErrorSeverity.HIGH,
            message="Image not found",
            details={"image": "test:latest"},
            retry_possible=True,
            suggested_action="Check image name",
            context=context
        )
        
        assert error.category == ErrorCategory.DOCKER_IMAGE
        assert error.severity == ErrorSeverity.HIGH
        assert error.message == "Image not found"
        assert error.details == {"image": "test:latest"}
        assert error.retry_possible is True
        assert error.suggested_action == "Check image name"
        assert error.context == context


class TestRetryStrategy:
    """Tests for RetryStrategy dataclass"""
    
    def test_retry_strategy_defaults(self):
        """Test RetryStrategy default values"""
        strategy = RetryStrategy()
        
        assert strategy.max_attempts == 3
        assert strategy.base_delay == 1.0
        assert strategy.max_delay == 30.0
        assert strategy.exponential_backoff is True
        assert strategy.retry_on_categories is None
    
    def test_retry_strategy_custom(self):
        """Test RetryStrategy with custom values"""
        categories = [ErrorCategory.NETWORK, ErrorCategory.DOCKER_DAEMON]
        strategy = RetryStrategy(
            max_attempts=5,
            base_delay=2.0,
            max_delay=60.0,
            exponential_backoff=False,
            retry_on_categories=categories
        )
        
        assert strategy.max_attempts == 5
        assert strategy.base_delay == 2.0
        assert strategy.max_delay == 60.0
        assert strategy.exponential_backoff is False
        assert strategy.retry_on_categories == categories


class TestPreparationErrorHandler:
    """Tests for PreparationErrorHandler class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.handler = PreparationErrorHandler()
    
    def test_initialization_default(self):
        """Test handler initialization with defaults"""
        handler = PreparationErrorHandler()
        
        assert isinstance(handler.retry_strategy, RetryStrategy)
        assert handler.retry_strategy.max_attempts == 3
        assert handler.error_history == []
        assert isinstance(handler.logger, logging.Logger)
    
    def test_initialization_custom_strategy(self):
        """Test handler initialization with custom retry strategy"""
        custom_strategy = RetryStrategy(max_attempts=5, base_delay=2.0)
        handler = PreparationErrorHandler(custom_strategy)
        
        assert handler.retry_strategy == custom_strategy
        assert handler.retry_strategy.max_attempts == 5
        assert handler.retry_strategy.base_delay == 2.0
    
    def test_handle_error_docker_daemon(self):
        """Test handling Docker daemon errors"""
        error = RuntimeError("Cannot connect to the Docker daemon")
        context = {"operation": "docker_start"}
        
        with patch.object(self.handler.logger, 'error') as mock_log:
            prep_error = self.handler.handle_error(error, context)
        
        assert prep_error.category == ErrorCategory.DOCKER_DAEMON
        assert prep_error.severity == ErrorSeverity.CRITICAL
        assert prep_error.message == "Docker daemon is not accessible"
        assert prep_error.retry_possible is True
        assert "Docker daemon" in prep_error.suggested_action
        assert prep_error.context == context
        assert len(self.handler.error_history) == 1
        
        # Verify logging
        mock_log.assert_called_once()
        call_args = mock_log.call_args
        assert "Preparation error" in call_args[0][0]
    
    def test_handle_error_docker_daemon_variations(self):
        """Test Docker daemon error variations"""
        daemon_errors = [
            "docker daemon is not running",
            "connection refused",
            "Cannot connect to the Docker daemon at unix:///var/run/docker.sock"
        ]
        
        for error_msg in daemon_errors:
            handler = PreparationErrorHandler()
            error = Exception(error_msg)
            prep_error = handler.handle_error(error, {})
            
            assert prep_error.category == ErrorCategory.DOCKER_DAEMON
            assert prep_error.severity == ErrorSeverity.CRITICAL
    
    def test_handle_error_docker_image(self):
        """Test handling Docker image errors"""
        error = RuntimeError("pull access denied for test-image")
        context = {"image": "test-image"}
        
        prep_error = self.handler.handle_error(error, context)
        
        assert prep_error.category == ErrorCategory.DOCKER_IMAGE
        assert prep_error.severity == ErrorSeverity.HIGH
        assert prep_error.message == "Docker image not available"
        assert prep_error.retry_possible is True
        assert "image name" in prep_error.suggested_action
    
    def test_handle_error_docker_image_variations(self):
        """Test Docker image error variations"""
        image_errors = [
            "no such image: test:latest",
            "repository does not exist",
            "image not found"
        ]
        
        for error_msg in image_errors:
            handler = PreparationErrorHandler()
            error = Exception(error_msg)
            prep_error = handler.handle_error(error, {})
            
            assert prep_error.category == ErrorCategory.DOCKER_IMAGE
            assert prep_error.severity == ErrorSeverity.HIGH
    
    def test_handle_error_docker_container(self):
        """Test handling Docker container errors"""
        error = RuntimeError("container already exists")
        context = {"container": "test-container"}
        
        prep_error = self.handler.handle_error(error, context)
        
        assert prep_error.category == ErrorCategory.DOCKER_CONTAINER
        assert prep_error.severity == ErrorSeverity.MEDIUM
        assert prep_error.message == "Docker container conflict"
        assert prep_error.retry_possible is True
        assert "container" in prep_error.suggested_action
    
    def test_handle_error_docker_container_variations(self):
        """Test Docker container error variations"""
        container_errors = [
            "container is running",
            "container not found",
            "conflict: unable to delete container"
        ]
        
        for error_msg in container_errors:
            handler = PreparationErrorHandler()
            error = Exception(error_msg)
            prep_error = handler.handle_error(error, {})
            
            assert prep_error.category == ErrorCategory.DOCKER_CONTAINER
            assert prep_error.severity == ErrorSeverity.MEDIUM
    
    def test_handle_error_filesystem(self):
        """Test handling filesystem errors"""
        error = PermissionError("permission denied")
        context = {"path": "/test/path"}
        
        prep_error = self.handler.handle_error(error, context)
        
        assert prep_error.category == ErrorCategory.FILESYSTEM
        assert prep_error.severity == ErrorSeverity.HIGH
        assert prep_error.message == "Filesystem operation failed"
        assert prep_error.retry_possible is False
        assert "permissions" in prep_error.suggested_action
    
    def test_handle_error_filesystem_variations(self):
        """Test filesystem error variations"""
        fs_errors = [
            "no such file or directory",
            "directory not empty",
            "out of disk space"  # Changed to match the pattern "disk space"
        ]
        
        for error_msg in fs_errors:
            handler = PreparationErrorHandler()
            error = Exception(error_msg)
            prep_error = handler.handle_error(error, {})
            
            assert prep_error.category == ErrorCategory.FILESYSTEM
            assert prep_error.severity == ErrorSeverity.HIGH
            assert prep_error.retry_possible is False
    
    def test_handle_error_network(self):
        """Test handling network errors"""
        error = TimeoutError("network timeout")
        context = {"url": "http://example.com"}
        
        prep_error = self.handler.handle_error(error, context)
        
        assert prep_error.category == ErrorCategory.NETWORK
        assert prep_error.severity == ErrorSeverity.MEDIUM
        assert prep_error.message == "Network operation failed"
        assert prep_error.retry_possible is True
        assert "network" in prep_error.suggested_action
    
    def test_handle_error_network_variations(self):
        """Test network error variations"""
        network_errors = [
            "connection timeout",
            "dns resolution failed",
            "network unreachable"
        ]
        
        for error_msg in network_errors:
            handler = PreparationErrorHandler()
            error = Exception(error_msg)
            prep_error = handler.handle_error(error, {})
            
            assert prep_error.category == ErrorCategory.NETWORK
            assert prep_error.severity == ErrorSeverity.MEDIUM
            assert prep_error.retry_possible is True
    
    def test_handle_error_resource(self):
        """Test handling resource errors"""
        error = MemoryError("out of memory")
        context = {"operation": "large_computation"}
        
        prep_error = self.handler.handle_error(error, context)
        
        assert prep_error.category == ErrorCategory.RESOURCE
        assert prep_error.severity == ErrorSeverity.HIGH
        assert prep_error.message == "Resource constraint encountered"
        assert prep_error.retry_possible is False
        assert "resources" in prep_error.suggested_action
    
    def test_handle_error_resource_variations(self):
        """Test resource error variations"""
        resource_errors = [
            "resource temporarily unavailable",
            "quota exceeded",
            "limit exceeded"
        ]
        
        for error_msg in resource_errors:
            handler = PreparationErrorHandler()
            error = Exception(error_msg)
            prep_error = handler.handle_error(error, {})
            
            assert prep_error.category == ErrorCategory.RESOURCE
            assert prep_error.severity == ErrorSeverity.HIGH
            assert prep_error.retry_possible is False
    
    def test_handle_error_generic(self):
        """Test handling generic errors"""
        error = ValueError("invalid configuration value")
        context = {"config": "test.yaml"}
        
        prep_error = self.handler.handle_error(error, context)
        
        assert prep_error.category == ErrorCategory.CONFIGURATION
        assert prep_error.severity == ErrorSeverity.MEDIUM
        assert prep_error.message == "invalid configuration value"
        assert prep_error.retry_possible is True
        assert "configuration" in prep_error.suggested_action
    
    def test_should_retry_max_attempts_exceeded(self):
        """Test should_retry when max attempts exceeded"""
        error = PreparationError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            details={},
            retry_possible=True
        )
        
        result = self.handler.should_retry(error, 3)  # At max attempts
        assert result is False
        
        result = self.handler.should_retry(error, 4)  # Over max attempts
        assert result is False
    
    def test_should_retry_not_retryable(self):
        """Test should_retry when error is not retryable"""
        error = PreparationError(
            category=ErrorCategory.FILESYSTEM,
            severity=ErrorSeverity.HIGH,
            message="Permission denied",
            details={},
            retry_possible=False
        )
        
        result = self.handler.should_retry(error, 1)
        assert result is False
    
    def test_should_retry_category_restriction(self):
        """Test should_retry with category restrictions"""
        strategy = RetryStrategy(retry_on_categories=[ErrorCategory.NETWORK])
        handler = PreparationErrorHandler(strategy)
        
        # Network error should be retryable
        network_error = PreparationError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            details={},
            retry_possible=True
        )
        
        result = handler.should_retry(network_error, 1)
        assert result is True
        
        # Filesystem error should not be retryable due to category restriction
        fs_error = PreparationError(
            category=ErrorCategory.FILESYSTEM,
            severity=ErrorSeverity.HIGH,
            message="File error",
            details={},
            retry_possible=True
        )
        
        result = handler.should_retry(fs_error, 1)
        assert result is False
    
    def test_should_retry_critical_error(self):
        """Test should_retry rejects critical errors"""
        error = PreparationError(
            category=ErrorCategory.DOCKER_DAEMON,
            severity=ErrorSeverity.CRITICAL,
            message="Critical error",
            details={},
            retry_possible=True
        )
        
        result = self.handler.should_retry(error, 1)
        assert result is False
    
    def test_should_retry_success_case(self):
        """Test should_retry allows retry in valid cases"""
        error = PreparationError(
            category=ErrorCategory.NETWORK,
            severity=ErrorSeverity.MEDIUM,
            message="Network error",
            details={},
            retry_possible=True
        )
        
        result = self.handler.should_retry(error, 1)
        assert result is True
        
        result = self.handler.should_retry(error, 2)
        assert result is True
    
    def test_get_retry_delay_exponential_backoff(self):
        """Test retry delay calculation with exponential backoff"""
        strategy = RetryStrategy(
            base_delay=2.0,
            max_delay=16.0,
            exponential_backoff=True
        )
        handler = PreparationErrorHandler(strategy)
        
        # Test exponential growth
        assert handler.get_retry_delay(1) == 2.0  # 2.0 * (2^0)
        assert handler.get_retry_delay(2) == 4.0  # 2.0 * (2^1)
        assert handler.get_retry_delay(3) == 8.0  # 2.0 * (2^2)
        assert handler.get_retry_delay(4) == 16.0  # 2.0 * (2^3) = 16.0, capped at max_delay
        assert handler.get_retry_delay(5) == 16.0  # Capped at max_delay
    
    def test_get_retry_delay_linear_backoff(self):
        """Test retry delay calculation with linear backoff"""
        strategy = RetryStrategy(
            base_delay=3.0,
            max_delay=10.0,
            exponential_backoff=False
        )
        handler = PreparationErrorHandler(strategy)
        
        # Test linear delay (always base_delay)
        assert handler.get_retry_delay(1) == 3.0
        assert handler.get_retry_delay(2) == 3.0
        assert handler.get_retry_delay(3) == 3.0
        assert handler.get_retry_delay(10) == 3.0
    
    def test_generate_error_report_no_errors(self):
        """Test error report generation with no errors"""
        report = self.handler.generate_error_report()
        
        assert report["status"] == "no_errors"
        assert report["errors"] == []
    
    def test_generate_error_report_with_errors(self):
        """Test error report generation with errors"""
        # Add some errors to history
        errors = [
            PreparationError(
                category=ErrorCategory.DOCKER_DAEMON,
                severity=ErrorSeverity.CRITICAL,
                message="Docker daemon error",
                details={},
                suggested_action="Start Docker"
            ),
            PreparationError(
                category=ErrorCategory.DOCKER_IMAGE,
                severity=ErrorSeverity.HIGH,
                message="Image not found",
                details={},
                suggested_action="Check image name"
            ),
            PreparationError(
                category=ErrorCategory.FILESYSTEM,
                severity=ErrorSeverity.HIGH,
                message="Permission denied",
                details={},
                suggested_action="Check permissions"
            )
        ]
        
        self.handler.error_history = errors
        
        report = self.handler.generate_error_report()
        
        assert report["status"] == "errors_found"
        assert report["total_errors"] == 3
        
        # Check categorization
        assert report["by_category"]["docker_daemon"] == 1
        assert report["by_category"]["docker_image"] == 1
        assert report["by_category"]["filesystem"] == 1
        
        # Check severity grouping
        assert report["by_severity"]["critical"] == 1
        assert report["by_severity"]["high"] == 2
        
        # Check recommendations
        recommendations = report["recommendations"]
        assert "Check Docker installation and daemon status" in recommendations
        assert "Verify Docker image names and availability" in recommendations
        assert "Check file permissions and disk space" in recommendations
        
        # Check error details
        assert len(report["errors"]) == 3
        for error_info in report["errors"]:
            assert "category" in error_info
            assert "severity" in error_info
            assert "message" in error_info
            assert "suggested_action" in error_info
    
    def test_generate_error_report_many_errors(self):
        """Test error report generation with many errors (>10)"""
        # Add 15 errors
        errors = []
        for i in range(15):
            errors.append(PreparationError(
                category=ErrorCategory.NETWORK,
                severity=ErrorSeverity.MEDIUM,
                message=f"Network error {i}",
                details={},
                suggested_action="Check network"
            ))
        
        self.handler.error_history = errors
        
        report = self.handler.generate_error_report()
        
        assert report["total_errors"] == 15
        assert len(report["errors"]) == 10  # Only last 10 errors
        
        # Check that it's the last 10
        reported_messages = [e["message"] for e in report["errors"]]
        expected_messages = [f"Network error {i}" for i in range(5, 15)]
        assert reported_messages == expected_messages


class TestRobustPreparationExecutor:
    """Tests for RobustPreparationExecutor class"""
    
    def setup_method(self):
        """Setup test environment"""
        self.mock_base_executor = Mock()
        self.mock_operations = Mock()
        self.mock_base_executor.operations = self.mock_operations
        
        self.executor = RobustPreparationExecutor(self.mock_base_executor)
    
    def test_initialization_default_error_handler(self):
        """Test initialization with default error handler"""
        executor = RobustPreparationExecutor(self.mock_base_executor)
        
        assert executor.base_executor == self.mock_base_executor
        assert isinstance(executor.error_handler, PreparationErrorHandler)
        assert isinstance(executor.logger, logging.Logger)
    
    def test_initialization_custom_error_handler(self):
        """Test initialization with custom error handler"""
        custom_handler = PreparationErrorHandler()
        executor = RobustPreparationExecutor(self.mock_base_executor, custom_handler)
        
        assert executor.error_handler == custom_handler
    
    def test_execute_with_retry_all_success(self):
        """Test execute_with_retry with all tasks succeeding"""
        # Create mock tasks
        tasks = []
        for i in range(3):
            task = Mock()
            task.task_id = f"task_{i}"
            task.request_object = Mock()
            
            # Mock successful execution
            result = Mock()
            result.success = True
            task.request_object.execute.return_value = result
            
            tasks.append(task)
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        # Execute with mocked time.sleep to speed up test
        with patch('time.sleep'):
            success, successful_tasks, failed_tasks = self.executor.execute_with_retry(tasks)
        
        assert success is True
        assert len(successful_tasks) == 3
        assert len(failed_tasks) == 0
        assert all(task in successful_tasks for task in tasks)
    
    def test_execute_with_retry_some_failures(self):
        """Test execute_with_retry with some task failures"""
        # Create mock tasks
        tasks = []
        for i in range(3):
            task = Mock()
            task.task_id = f"task_{i}"
            task.task_type = "test_type"
            task.description = f"Test task {i}"
            task.request_object = Mock()
            
            # First task succeeds, others fail
            if i == 0:
                result = Mock()
                result.success = True
                task.request_object.execute.return_value = result
            else:
                result = Mock()
                result.success = False
                result.stderr = f"Error in task {i}"
                task.request_object.execute.return_value = result
            
            tasks.append(task)
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        # Execute with mocked time.sleep to speed up test
        with patch('time.sleep'):
            success, successful_tasks, failed_tasks = self.executor.execute_with_retry(tasks)
        
        assert success is False
        assert len(successful_tasks) == 1
        assert len(failed_tasks) == 2
        assert tasks[0] in successful_tasks
        assert tasks[1] in failed_tasks
        assert tasks[2] in failed_tasks
    
    def test_execute_task_with_retry_success_first_attempt(self):
        """Test _execute_task_with_retry succeeding on first attempt"""
        task = Mock()
        task.task_id = "test_task"
        task.request_object = Mock()
        
        # Mock successful execution
        result = Mock()
        result.success = True
        task.request_object.execute.return_value = result
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        with patch.object(self.executor.logger, 'info') as mock_log:
            success = self.executor._execute_task_with_retry(task, 3)
        
        assert success is True
        task.request_object.execute.assert_called_once_with(mock_driver)
        mock_log.assert_called_once_with("Task test_task succeeded on attempt 1")
    
    def test_execute_task_with_retry_success_after_retries(self):
        """Test _execute_task_with_retry succeeding after retries"""
        task = Mock()
        task.task_id = "test_task"
        task.task_type = "test_type"
        task.description = "Test task"
        task.request_object = Mock()
        
        # Mock failure then success
        failure_result = Mock()
        failure_result.success = False
        failure_result.stderr = "Temporary failure"
        
        success_result = Mock()
        success_result.success = True
        
        task.request_object.execute.side_effect = [failure_result, success_result]
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        # Mock error handler to allow retry
        mock_error = Mock()
        mock_error.retry_possible = True
        mock_error.severity = ErrorSeverity.MEDIUM
        
        with patch.object(self.executor.error_handler, 'handle_error', return_value=mock_error):
            with patch.object(self.executor.error_handler, 'should_retry', return_value=True):
                with patch.object(self.executor.error_handler, 'get_retry_delay', return_value=0.01):
                    with patch('time.sleep'):  # Speed up test
                        with patch.object(self.executor.logger, 'warning') as mock_warning:
                            with patch.object(self.executor.logger, 'info') as mock_info:
                                success = self.executor._execute_task_with_retry(task, 3)
        
        assert success is True
        assert task.request_object.execute.call_count == 2
        mock_warning.assert_called_once()
        mock_info.assert_called_once()
    
    def test_execute_task_with_retry_permanent_failure(self):
        """Test _execute_task_with_retry with permanent failure"""
        task = Mock()
        task.task_id = "test_task"
        task.task_type = "test_type"
        task.description = "Test task"
        task.request_object = Mock()
        
        # Mock consistent failure
        failure_result = Mock()
        failure_result.success = False
        failure_result.stderr = "Permanent failure"
        task.request_object.execute.return_value = failure_result
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        # Mock error handler to disallow retry
        mock_error = Mock()
        mock_error.retry_possible = False
        
        with patch.object(self.executor.error_handler, 'handle_error', return_value=mock_error):
            with patch.object(self.executor.error_handler, 'should_retry', return_value=False):
                with patch.object(self.executor.logger, 'error') as mock_error_log:
                    success = self.executor._execute_task_with_retry(task, 3)
        
        assert success is False
        assert task.request_object.execute.call_count == 1
        mock_error_log.assert_called_once()
        assert "failed permanently after 1 attempts" in mock_error_log.call_args[0][0]
    
    def test_execute_task_with_retry_max_retries_exceeded(self):
        """Test _execute_task_with_retry exceeding max retries"""
        task = Mock()
        task.task_id = "test_task"
        task.task_type = "test_type"
        task.description = "Test task"
        task.request_object = Mock()
        
        # Mock consistent failure
        failure_result = Mock()
        failure_result.success = False
        failure_result.stderr = "Consistent failure"
        task.request_object.execute.return_value = failure_result
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        # Mock error handler to allow retries initially
        mock_error = Mock()
        mock_error.retry_possible = True
        
        def should_retry_side_effect(error, attempt):
            return attempt < 3  # Allow 2 retries, fail on 3rd
        
        with patch.object(self.executor.error_handler, 'handle_error', return_value=mock_error):
            with patch.object(self.executor.error_handler, 'should_retry', side_effect=should_retry_side_effect):
                with patch.object(self.executor.error_handler, 'get_retry_delay', return_value=0.01):
                    with patch('time.sleep'):  # Speed up test
                        with patch.object(self.executor.logger, 'warning') as mock_warning:
                            with patch.object(self.executor.logger, 'error') as mock_error_log:
                                success = self.executor._execute_task_with_retry(task, 3)
        
        assert success is False
        assert task.request_object.execute.call_count == 3
        assert mock_warning.call_count == 2  # Two retry warnings
        mock_error_log.assert_called_once()
    
    def test_execute_task_with_retry_exception_handling(self):
        """Test _execute_task_with_retry with exception during execution"""
        task = Mock()
        task.task_id = "test_task"
        task.task_type = "test_type"
        task.description = "Test task"
        task.request_object = Mock()
        
        # Mock exception during execution
        task.request_object.execute.side_effect = RuntimeError("Execution exception")
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        # Mock error handler to disallow retry
        mock_error = Mock()
        mock_error.retry_possible = False
        
        with patch.object(self.executor.error_handler, 'handle_error', return_value=mock_error):
            with patch.object(self.executor.error_handler, 'should_retry', return_value=False):
                with patch.object(self.executor.logger, 'error') as mock_error_log:
                    success = self.executor._execute_task_with_retry(task, 3)
        
        assert success is False
        mock_error_log.assert_called_once()
    
    def test_execute_task_with_retry_exception_with_retries(self):
        """Test _execute_task_with_retry with exceptions and retries"""
        task = Mock()
        task.task_id = "test_task"
        task.task_type = "test_type"
        task.description = "Test task"
        task.request_object = Mock()
        
        # Mock exception then success
        success_result = Mock()
        success_result.success = True
        
        task.request_object.execute.side_effect = [RuntimeError("Temporary exception"), success_result]
        
        # Mock unified driver
        mock_driver = Mock()
        self.mock_operations.resolve.return_value = mock_driver
        
        # Mock error handler to allow retry
        mock_error = Mock()
        mock_error.retry_possible = True
        
        with patch.object(self.executor.error_handler, 'handle_error', return_value=mock_error):
            with patch.object(self.executor.error_handler, 'should_retry', return_value=True):
                with patch.object(self.executor.error_handler, 'get_retry_delay', return_value=0.01):
                    with patch('time.sleep'):  # Speed up test
                        success = self.executor._execute_task_with_retry(task, 3)
        
        assert success is True
        assert task.request_object.execute.call_count == 2


class TestIntegrationScenarios:
    """Integration tests for complex error handling scenarios"""
    
    def test_docker_workflow_with_cascading_failures(self):
        """Test handling cascading Docker-related failures"""
        strategy = RetryStrategy(
            max_attempts=2,
            base_delay=0.01,  # Fast for testing
            retry_on_categories=[ErrorCategory.DOCKER_DAEMON, ErrorCategory.NETWORK]
        )
        handler = PreparationErrorHandler(strategy)
        
        # Simulate Docker daemon failure followed by network issue
        errors = [
            Exception("Cannot connect to the Docker daemon"),
            Exception("network timeout"),
            Exception("permission denied")  # Should not retry
        ]
        
        context = {"workflow": "docker_setup"}
        
        for error in errors:
            prep_error = handler.handle_error(error, context)
            
            if prep_error.category == ErrorCategory.DOCKER_DAEMON:
                assert handler.should_retry(prep_error, 1) is False  # Critical error
            elif prep_error.category == ErrorCategory.NETWORK:
                assert handler.should_retry(prep_error, 1) is True
            elif prep_error.category == ErrorCategory.FILESYSTEM:
                assert handler.should_retry(prep_error, 1) is False  # Not retryable
        
        # Verify error history and reporting
        assert len(handler.error_history) == 3
        report = handler.generate_error_report()
        assert report["by_category"]["docker_daemon"] == 1
        assert report["by_category"]["network"] == 1
        assert report["by_category"]["filesystem"] == 1
    
    def test_robust_executor_resilience_workflow(self):
        """Test robust executor handling mixed success/failure scenarios"""
        base_executor = Mock()
        base_executor.operations.resolve.return_value = Mock()
        
        # Custom retry strategy for testing
        strategy = RetryStrategy(max_attempts=2, base_delay=0.01)
        error_handler = PreparationErrorHandler(strategy)
        
        executor = RobustPreparationExecutor(base_executor, error_handler)
        
        # Create varied tasks
        tasks = []
        for i in range(4):
            task = Mock()
            task.task_id = f"task_{i}"
            task.task_type = "test"
            task.description = f"Test task {i}"
            task.request_object = Mock()
            
            if i == 0:
                # Success on first try
                result = Mock()
                result.success = True
                task.request_object.execute.return_value = result
            elif i == 1:
                # Failure then success
                failure = Mock()
                failure.success = False
                failure.stderr = "network timeout"
                success = Mock()
                success.success = True
                task.request_object.execute.side_effect = [failure, success]
            elif i == 2:
                # Permanent failure
                failure = Mock()
                failure.success = False
                failure.stderr = "permission denied"
                task.request_object.execute.return_value = failure
            else:
                # Exception then success
                success = Mock()
                success.success = True
                task.request_object.execute.side_effect = [RuntimeError("temporary error"), success]
            
            tasks.append(task)
        
        with patch('time.sleep'):  # Speed up test
            success, successful, failed = executor.execute_with_retry(tasks, max_retries=2)
        
        # Should have mixed results
        assert not success  # Overall failure due to one permanent failure
        assert len(successful) == 3  # task_0, task_1, task_3
        assert len(failed) == 1  # task_2
        
        # Verify error handler was used
        assert len(error_handler.error_history) > 0
        
        # Generate report
        report = error_handler.generate_error_report()
        assert report["status"] == "errors_found"