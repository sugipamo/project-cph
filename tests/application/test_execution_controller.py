"""Tests for ExecutionController."""
from unittest.mock import MagicMock

import pytest

from src.application.orchestration.execution_controller import ExecutionController
from src.domain.exceptions.composite_step_failure import CompositeStepFailureError


class TestExecutionController:
    """Test ExecutionController functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.controller = ExecutionController()

    def test_execute_requests_success(self):
        """Test successful execution of requests."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_request1 = MagicMock()
        mock_request2 = MagicMock()
        mock_result1 = MagicMock()
        mock_result2 = MagicMock()

        # Configure success results
        mock_result1.success = True
        mock_result2.success = True
        mock_request1.execute.return_value = mock_result1
        mock_request2.execute.return_value = mock_result2
        mock_request1.allow_failure = False
        mock_request2.allow_failure = False

        requests = [mock_request1, mock_request2]

        # Execute
        results = self.controller.execute_requests(requests, mock_driver)

        # Assert
        assert len(results) == 2
        assert results[0] == mock_result1
        assert results[1] == mock_result2

        mock_request1.execute.assert_called_once_with(driver=mock_driver)
        mock_request2.execute.assert_called_once_with(driver=mock_driver)

    def test_execute_requests_failure_not_allowed(self):
        """Test execution failure when allow_failure is False."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_request = MagicMock()
        mock_result = MagicMock()

        # Configure failed result
        mock_result.success = False
        mock_request.execute_operation.return_value = mock_result
        mock_request.allow_failure = False

        requests = [mock_request]

        # Execute and expect exception
        with pytest.raises(CompositeStepFailureError) as exc_info:
            self.controller.execute_requests(requests, mock_driver)

        assert "Step failed" in str(exc_info.value)
        assert exc_info.value.result == mock_result

    def test_execute_requests_failure_allowed(self):
        """Test execution continues when allow_failure is True."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_request1 = MagicMock()
        mock_request2 = MagicMock()
        mock_result1 = MagicMock()
        mock_result2 = MagicMock()

        # First request fails but allows failure
        mock_result1.success = False
        mock_request1.execute.return_value = mock_result1
        mock_request1.allow_failure = True

        # Second request succeeds
        mock_result2.success = True
        mock_request2.execute.return_value = mock_result2
        mock_request2.allow_failure = False

        requests = [mock_request1, mock_request2]

        # Execute
        results = self.controller.execute_requests(requests, mock_driver)

        # Assert both requests were executed
        assert len(results) == 2
        assert results[0] == mock_result1
        assert results[1] == mock_result2

    def test_execute_requests_no_success_attribute(self):
        """Test execution with result that has no success attribute."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_request = MagicMock()
        mock_result = MagicMock()

        # Remove success attribute
        del mock_result.success
        mock_request.execute_operation.return_value = mock_result
        mock_request.allow_failure = False

        requests = [mock_request]

        # Execute and expect exception (since no success attribute means failure)
        with pytest.raises(CompositeStepFailureError):
            self.controller.execute_requests(requests, mock_driver)

    def test_execute_requests_no_allow_failure_attribute(self):
        """Test execution with request that has no allow_failure attribute."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_request = MagicMock()
        mock_result = MagicMock()

        # Configure failed result, no allow_failure attribute (defaults to False)
        mock_result.success = False
        mock_request.execute_operation.return_value = mock_result
        del mock_request.allow_failure  # Remove attribute

        requests = [mock_request]

        # Execute and expect exception (allow_failure defaults to False)
        with pytest.raises(CompositeStepFailureError):
            self.controller.execute_requests(requests, mock_driver)

    def test_execute_requests_mixed_success_and_failure(self):
        """Test execution with mixed success and failure scenarios."""
        # Setup mocks
        mock_driver = MagicMock()
        mock_request1 = MagicMock()
        mock_request2 = MagicMock()
        mock_request3 = MagicMock()
        mock_result1 = MagicMock()
        mock_result2 = MagicMock()

        # First request succeeds
        mock_result1.success = True
        mock_request1.execute.return_value = mock_result1
        mock_request1.allow_failure = False

        # Second request fails and doesn't allow failure
        mock_result2.success = False
        mock_request2.execute.return_value = mock_result2
        mock_request2.allow_failure = False

        requests = [mock_request1, mock_request2, mock_request3]

        # Execute and expect exception after second request
        with pytest.raises(CompositeStepFailureError):
            self.controller.execute_requests(requests, mock_driver)

        # Verify first request was executed, second failed, third was not executed
        mock_request1.execute.assert_called_once_with(driver=mock_driver)
        mock_request2.execute.assert_called_once_with(driver=mock_driver)
        mock_request3.execute.assert_not_called()

    def test_check_failure_success(self):
        """Test _check_failure with successful result."""
        mock_request = MagicMock()
        mock_result = MagicMock()
        mock_result.success = True
        mock_request.allow_failure = False

        # Should not raise exception
        self.controller._check_failure(mock_request, mock_result)

    def test_check_failure_allowed_failure(self):
        """Test _check_failure with allowed failure."""
        mock_request = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_request.allow_failure = True

        # Should not raise exception
        self.controller._check_failure(mock_request, mock_result)

    def test_check_failure_not_allowed_failure(self):
        """Test _check_failure with not allowed failure."""
        mock_request = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        mock_request.allow_failure = False

        # Should raise exception
        with pytest.raises(CompositeStepFailureError) as exc_info:
            self.controller._check_failure(mock_request, mock_result)

        assert "Step failed" in str(exc_info.value)
        assert "allow_failure=False" in str(exc_info.value)
        assert exc_info.value.result == mock_result

    def test_check_failure_default_allow_failure(self):
        """Test _check_failure with default allow_failure (False)."""
        mock_request = MagicMock()
        mock_result = MagicMock()
        mock_result.success = False
        # No allow_failure attribute - should default to False
        delattr(mock_request, 'allow_failure')

        # Should raise exception
        with pytest.raises(CompositeStepFailureError):
            self.controller._check_failure(mock_request, mock_result)

    def test_check_failure_no_success_attribute(self):
        """Test _check_failure with result that has no success attribute."""
        mock_request = MagicMock()
        mock_result = MagicMock()
        # No success attribute
        delattr(mock_result, 'success')
        mock_request.allow_failure = False

        # Should raise exception since no success attribute implies failure
        with pytest.raises(CompositeStepFailureError):
            self.controller._check_failure(mock_request, mock_result)

    def test_execute_requests_empty_list(self):
        """Test execution with empty request list."""
        mock_driver = MagicMock()
        requests = []

        results = self.controller.execute_requests(requests, mock_driver)

        assert results == []

    def test_execute_requests_single_request(self):
        """Test execution with single request."""
        mock_driver = MagicMock()
        mock_request = MagicMock()
        mock_result = MagicMock()

        mock_result.success = True
        mock_request.execute_operation.return_value = mock_result
        mock_request.allow_failure = False

        requests = [mock_request]

        results = self.controller.execute_requests(requests, mock_driver)

        assert len(results) == 1
        assert results[0] == mock_result
        mock_request.execute_operation.assert_called_once_with(driver=mock_driver)
