import pytest
from src.domain.composite_step_failure import CompositeStepFailureError


class TestCompositeStepFailure:
    def test_init_with_message_only(self):
        failure = CompositeStepFailureError("Test failure message")
        
        assert str(failure) == "Test failure message"

    def test_init_with_context(self):
        failure = CompositeStepFailureError("Test failure", context="test context")
        
        assert str(failure) == "Test failure"

    def test_init_with_result(self):
        result = {"status": "failed", "code": 1}
        failure = CompositeStepFailureError("Test failure", result=result)
        
        assert str(failure) == "Test failure"

    def test_init_with_original_exception(self):
        original = ValueError("Original error")
        failure = CompositeStepFailureError("Wrapped error", original_exception=original)
        
        assert str(failure) == "Wrapped error"

    def test_inheritance_from_exception(self):
        failure = CompositeStepFailureError("Test")
        
        assert isinstance(failure, Exception)

    def test_can_be_raised(self):
        with pytest.raises(CompositeStepFailureError) as exc_info:
            raise CompositeStepFailureError("Test error")
        
        assert str(exc_info.value) == "Test error"

    def test_can_be_caught_as_exception(self):
        try:
            raise CompositeStepFailureError("Test error")
        except Exception as e:
            assert isinstance(e, CompositeStepFailureError)
            assert str(e) == "Test error"