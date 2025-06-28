import pytest
from src.operations.path_types import PathOperationResult


class TestPathOperationResult:
    def test_path_operation_result_initialization(self):
        """Test PathOperationResult initialization"""
        result = PathOperationResult(
            success=True,
            result="test_result",
            errors=["error1"],
            warnings=["warning1"],
            metadata={"key": "value"}
        )
        assert result.success is True
        assert result.result == "test_result"
        assert result.errors == ["error1"]
        assert result.warnings == ["warning1"]
        assert result.metadata == {"key": "value"}
    
    def test_path_operation_result_frozen(self):
        """Test that PathOperationResult is frozen (immutable)"""
        result = PathOperationResult(
            success=True,
            result="test",
            errors=[],
            warnings=[],
            metadata={}
        )
        with pytest.raises(AttributeError):
            result.success = False
    
    def test_path_operation_result_none_defaults(self):
        """Test PathOperationResult with None values"""
        result = PathOperationResult(
            success=False,
            result=None,
            errors=None,
            warnings=None,
            metadata=None
        )
        assert result.success is False
        assert result.result is None
        assert result.errors == []  # Should be converted to empty list
        assert result.warnings == []  # Should be converted to empty list
        assert result.metadata == {}  # Should be converted to empty dict
    
    def test_path_operation_result_equality(self):
        """Test PathOperationResult equality"""
        result1 = PathOperationResult(True, "test", [], [], {})
        result2 = PathOperationResult(True, "test", [], [], {})
        result3 = PathOperationResult(False, "test", [], [], {})
        
        assert result1 == result2
        assert result1 != result3