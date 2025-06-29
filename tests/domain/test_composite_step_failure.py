import pytest
from src.domain.composite_step_failure import CompositeStepFailureError
from src.operations.error_codes import ErrorCode


class TestCompositeStepFailure:
    def test_init_with_all_parameters(self):
        failure = CompositeStepFailureError(
            message="Test failure message",
            result=None,
            original_exception=None,
            error_code=ErrorCode.UNKNOWN_ERROR,
            context="test context"
        )
        
        assert str(failure) == "Test failure message"
        assert failure.result is None
        assert failure.original_exception is None
        assert failure.error_code == ErrorCode.UNKNOWN_ERROR
        assert failure.context == "test context"

    def test_init_with_result(self):
        result = {"status": "failed", "code": 1}
        failure = CompositeStepFailureError(
            message="Test failure",
            result=result,
            original_exception=None,
            error_code=ErrorCode.SHELL_EXECUTION_ERROR,
            context="test context"
        )
        
        assert str(failure) == "Test failure"
        assert failure.result == result

    def test_init_with_original_exception(self):
        original = FileNotFoundError("file not found")
        failure = CompositeStepFailureError(
            message="Wrapped error",
            result=None,
            original_exception=original,
            error_code=None,  # Should be classified from exception
            context="test context"
        )
        
        assert str(failure) == "Wrapped error"
        assert failure.original_exception == original
        assert failure.error_code == ErrorCode.FILE_NOT_FOUND  # Should be classified

    def test_get_suggestion(self):
        failure = CompositeStepFailureError(
            message="Test error",
            result=None,
            original_exception=None,
            error_code=ErrorCode.FILE_NOT_FOUND,
            context="test context"
        )
        
        suggestion = failure.get_suggestion()
        assert isinstance(suggestion, str)
        assert len(suggestion) > 0

    def test_get_formatted_message(self):
        failure = CompositeStepFailureError(
            message="Test error",
            result=None,
            original_exception=None,
            error_code=ErrorCode.FILE_PERMISSION_DENIED,
            context="test context"
        )
        
        formatted = failure.get_formatted_message()
        assert "[FILE_PERMISSION_DENIED#" in formatted
        assert "Test error" in formatted
        assert "提案:" in formatted

    def test_error_id_is_unique(self):
        failure1 = CompositeStepFailureError(
            message="Test 1",
            result=None,
            original_exception=None,
            error_code=ErrorCode.UNKNOWN_ERROR,
            context="test"
        )
        failure2 = CompositeStepFailureError(
            message="Test 2",
            result=None,
            original_exception=None,
            error_code=ErrorCode.UNKNOWN_ERROR,
            context="test"
        )
        
        assert failure1.error_id != failure2.error_id

    def test_inheritance_from_exception(self):
        failure = CompositeStepFailureError(
            message="Test",
            result=None,
            original_exception=None,
            error_code=ErrorCode.UNKNOWN_ERROR,
            context="test"
        )
        
        assert isinstance(failure, Exception)

    def test_can_be_raised(self):
        with pytest.raises(CompositeStepFailureError) as exc_info:
            raise CompositeStepFailureError(
                message="Test error",
                result=None,
                original_exception=None,
                error_code=ErrorCode.UNKNOWN_ERROR,
                context="test"
            )
        
        assert str(exc_info.value) == "Test error"

    def test_can_be_caught_as_exception(self):
        try:
            raise CompositeStepFailureError(
                message="Test error",
                result=None,
                original_exception=None,
                error_code=ErrorCode.UNKNOWN_ERROR,
                context="test"
            )
        except Exception as e:
            assert isinstance(e, CompositeStepFailureError)
            assert str(e) == "Test error"