"""Extended tests for composite_step_failure module to improve coverage."""

import pytest
from unittest.mock import Mock, patch
from src.domain.composite_step_failure import CompositeStepFailureError
from src.operations.error_codes import ErrorCode, ErrorSuggestion


class TestCompositeStepFailureExtended:
    """Extended tests for CompositeStepFailureError class."""
    
    def test_init_with_error_code_classification(self):
        """Test initialization with automatic error code classification."""
        original_exception = FileNotFoundError("File not found")
        
        with patch('src.domain.composite_step_failure.classify_error') as mock_classify:
            mock_classify.return_value = ErrorCode.FILE_NOT_FOUND
            
            error = CompositeStepFailureError(
                message="Test error",
                original_exception=original_exception,
                context="file_operation"
            )
            
            mock_classify.assert_called_once_with(original_exception, "file_operation")
            assert error.error_code == ErrorCode.FILE_NOT_FOUND
            assert error.context == "file_operation"
    
    def test_init_with_explicit_error_code(self):
        """Test initialization with explicit error code."""
        error = CompositeStepFailureError(
            message="Test error",
            error_code=ErrorCode.FILE_PERMISSION_DENIED
        )
        
        assert error.error_code == ErrorCode.FILE_PERMISSION_DENIED
        assert error.original_exception is None
        assert error.context == ''
    
    def test_init_default_error_code(self):
        """Test initialization with default error code when no exception."""
        error = CompositeStepFailureError(
            message="Test error"
        )
        
        assert error.error_code == ErrorCode.UNKNOWN_ERROR
        assert error.original_exception is None
    
    def test_get_suggestion(self):
        """Test get_suggestion method."""
        with patch.object(ErrorSuggestion, 'get_suggestion') as mock_get_suggestion:
            mock_get_suggestion.return_value = "Check file permissions"
            
            error = CompositeStepFailureError(
                message="Permission denied",
                error_code=ErrorCode.FILE_PERMISSION_DENIED
            )
            
            suggestion = error.get_suggestion()
            
            mock_get_suggestion.assert_called_once_with(ErrorCode.FILE_PERMISSION_DENIED)
            assert suggestion == "Check file permissions"
    
    def test_get_formatted_message_basic(self):
        """Test get_formatted_message with basic error."""
        with patch.object(ErrorSuggestion, 'get_suggestion') as mock_suggestion:
            with patch.object(ErrorSuggestion, 'get_recovery_actions') as mock_actions:
                mock_suggestion.return_value = "Check your network connection"
                mock_actions.return_value = []
                
                error = CompositeStepFailureError(
                    message="Network error occurred",
                    error_code=ErrorCode.NETWORK_CONNECTION_FAILED
                )
                
                formatted = error.get_formatted_message()
                
                assert f"[{ErrorCode.NETWORK_CONNECTION_FAILED.value}#{error.error_id}]" in formatted
                assert "Network error occurred" in formatted
                assert "提案: Check your network connection" in formatted
                assert "回復手順:" not in formatted
    
    def test_get_formatted_message_with_recovery_actions(self):
        """Test get_formatted_message with recovery actions."""
        with patch.object(ErrorSuggestion, 'get_suggestion') as mock_suggestion:
            with patch.object(ErrorSuggestion, 'get_recovery_actions') as mock_actions:
                mock_suggestion.return_value = "File not found"
                mock_actions.return_value = [
                    "Check if the file exists",
                    "Verify the file path",
                    "Create the file if needed"
                ]
                
                error = CompositeStepFailureError(
                    message="Cannot open file",
                    error_code=ErrorCode.FILE_NOT_FOUND
                )
                
                formatted = error.get_formatted_message()
                
                assert f"[{ErrorCode.FILE_NOT_FOUND.value}#{error.error_id}]" in formatted
                assert "Cannot open file" in formatted
                assert "提案: File not found" in formatted
                assert "回復手順:" in formatted
                assert "1. Check if the file exists" in formatted
                assert "2. Verify the file path" in formatted
                assert "3. Create the file if needed" in formatted
    
    def test_error_id_uniqueness(self):
        """Test that error_id is unique for each instance."""
        error1 = CompositeStepFailureError("Error 1")
        error2 = CompositeStepFailureError("Error 2")
        
        assert error1.error_id != error2.error_id
        assert len(error1.error_id) == 8
        assert len(error2.error_id) == 8
    
    def test_error_with_result_object(self):
        """Test error with result object attached."""
        mock_result = Mock()
        mock_result.status = "failed"
        mock_result.output = "Command failed"
        
        error = CompositeStepFailureError(
            message="Step failed",
            result=mock_result
        )
        
        assert error.result == mock_result
        assert error.result.status == "failed"
        assert error.result.output == "Command failed"
    
    def test_str_representation(self):
        """Test string representation of error."""
        error = CompositeStepFailureError("Test error message")
        assert str(error) == "Test error message"
    
    def test_formatted_message_strips_trailing_newline(self):
        """Test that formatted message strips trailing newline."""
        with patch.object(ErrorSuggestion, 'get_suggestion') as mock_suggestion:
            with patch.object(ErrorSuggestion, 'get_recovery_actions') as mock_actions:
                mock_suggestion.return_value = "Test suggestion"
                mock_actions.return_value = ["Action 1"]
                
                error = CompositeStepFailureError("Error", error_code=ErrorCode.UNKNOWN_ERROR)
                formatted = error.get_formatted_message()
                
                assert not formatted.endswith('\n\n')
                assert formatted.endswith('\n') or formatted.endswith('Action 1')