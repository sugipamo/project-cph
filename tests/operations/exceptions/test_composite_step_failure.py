"""
Tests for CompositeStepFailure exception
"""
import pytest
from src.domain.exceptions.composite_step_failure import CompositeStepFailure


class TestCompositeStepFailure:
    
    def test_init_with_message_only(self):
        """Test initialization with message only"""
        exc = CompositeStepFailure("Test error message")
        
        assert str(exc) == "Test error message"
        assert exc.result is None
        assert exc.original_exception is None
    
    def test_init_with_result(self):
        """Test initialization with result"""
        mock_result = {"status": "failed", "error": "Command not found"}
        exc = CompositeStepFailure("Step failed", result=mock_result)
        
        assert str(exc) == "Step failed"
        assert exc.result == mock_result
        assert exc.original_exception is None
    
    def test_init_with_original_exception(self):
        """Test initialization with original exception"""
        original = ValueError("Original error")
        exc = CompositeStepFailure("Wrapper error", original_exception=original)
        
        assert str(exc) == "Wrapper error"
        assert exc.result is None
        assert exc.original_exception is original
    
    def test_init_with_all_parameters(self):
        """Test initialization with all parameters"""
        mock_result = {"status": "failed"}
        original = RuntimeError("Runtime error")
        exc = CompositeStepFailure(
            "Complete failure",
            result=mock_result,
            original_exception=original
        )
        
        assert str(exc) == "Complete failure"
        assert exc.result == mock_result
        assert exc.original_exception is original
    
    def test_inheritance(self):
        """Test that CompositeStepFailure inherits from Exception"""
        exc = CompositeStepFailure("Test")
        
        assert isinstance(exc, Exception)
        assert isinstance(exc, CompositeStepFailure)
    
    def test_raise_and_catch(self):
        """Test raising and catching the exception"""
        mock_result = {"returncode": 1}
        
        with pytest.raises(CompositeStepFailure) as exc_info:
            raise CompositeStepFailure(
                "Command failed",
                result=mock_result
            )
        
        caught_exc = exc_info.value
        assert str(caught_exc) == "Command failed"
        assert caught_exc.result == mock_result
    
    def test_exception_chaining(self):
        """Test exception chaining with original exception"""
        try:
            # Simulate original error
            raise ValueError("Original error")
        except ValueError as e:
            # Wrap in CompositeStepFailure
            with pytest.raises(CompositeStepFailure) as exc_info:
                raise CompositeStepFailure(
                    "Step failed due to value error",
                    original_exception=e
                )
            
            caught_exc = exc_info.value
            assert caught_exc.original_exception is e
            assert str(caught_exc.original_exception) == "Original error"
    
    def test_empty_message(self):
        """Test with empty message"""
        exc = CompositeStepFailure("")
        
        assert str(exc) == ""
        assert exc.result is None
        assert exc.original_exception is None
    
    def test_complex_result_object(self):
        """Test with complex result object"""
        from unittest.mock import Mock
        
        mock_result = Mock()
        mock_result.success = False
        mock_result.stdout = "Output"
        mock_result.stderr = "Error output"
        mock_result.returncode = 1
        
        exc = CompositeStepFailure(
            "Execution failed",
            result=mock_result
        )
        
        assert exc.result is mock_result
        assert exc.result.success is False
        assert exc.result.returncode == 1