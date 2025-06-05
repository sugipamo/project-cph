"""
Comprehensive tests for validation module
"""
import pytest
from dataclasses import dataclass
from typing import Any, Dict
from src.pure_functions.formatting.core.validation import (
    validate_format_data,
    FormatDataValidator
)


# Test data classes
@dataclass
class SampleDataClass:
    name: str
    value: int
    optional: str = None


class SampleObject:
    def __init__(self, name: str, value: int):
        self.name = name
        self.value = value


class TestValidateFormatData:
    """Test validate_format_data function"""
    
    def test_validate_none_data(self):
        """Test validation of None data"""
        is_valid, error = validate_format_data(None, ["field"])
        assert is_valid is False
        assert error == "Data cannot be None"
    
    def test_validate_dataclass_success(self):
        """Test successful dataclass validation"""
        data = SampleDataClass(name="test", value=42)
        is_valid, error = validate_format_data(data, ["name", "value"])
        assert is_valid is True
        assert error is None
    
    def test_validate_dataclass_missing_field(self):
        """Test dataclass validation with missing field"""
        data = SampleDataClass(name="test", value=42)
        is_valid, error = validate_format_data(data, ["name", "missing"])
        assert is_valid is False
        assert "Required field 'missing' is missing" in error
    
    def test_validate_dataclass_empty_field(self):
        """Test dataclass validation with empty string field"""
        data = SampleDataClass(name="", value=42)
        is_valid, error = validate_format_data(data, ["name"])
        assert is_valid is False
        assert "Required field 'name' is empty" in error
    
    def test_validate_dataclass_whitespace_field(self):
        """Test dataclass validation with whitespace-only field"""
        data = SampleDataClass(name="   ", value=42)
        is_valid, error = validate_format_data(data, ["name"])
        assert is_valid is False
        assert "Required field 'name' is empty" in error
    
    def test_validate_dataclass_none_field(self):
        """Test dataclass validation with None field"""
        data = SampleDataClass(name="test", value=42)
        data.optional = None
        is_valid, error = validate_format_data(data, ["optional"])
        assert is_valid is False
        assert "Required field 'optional' is empty" in error
    
    def test_validate_dict_success(self):
        """Test successful dictionary validation"""
        data = {"name": "test", "value": 42}
        is_valid, error = validate_format_data(data, ["name", "value"])
        assert is_valid is True
        assert error is None
    
    def test_validate_dict_missing_key(self):
        """Test dictionary validation with missing key"""
        data = {"name": "test"}
        is_valid, error = validate_format_data(data, ["name", "missing"])
        assert is_valid is False
        assert "Required key 'missing' is missing" in error
    
    def test_validate_dict_empty_value(self):
        """Test dictionary validation with empty value"""
        data = {"name": "", "value": 42}
        is_valid, error = validate_format_data(data, ["name"])
        assert is_valid is False
        assert "Required key 'name' is empty" in error
    
    def test_validate_dict_none_value(self):
        """Test dictionary validation with None value"""
        data = {"name": None, "value": 42}
        is_valid, error = validate_format_data(data, ["name"])
        assert is_valid is False
        assert "Required key 'name' is empty" in error
    
    def test_validate_object_success(self):
        """Test successful object validation"""
        data = SampleObject(name="test", value=42)
        is_valid, error = validate_format_data(data, ["name", "value"])
        assert is_valid is True
        assert error is None
    
    def test_validate_object_missing_attribute(self):
        """Test object validation with missing attribute"""
        data = SampleObject(name="test", value=42)
        is_valid, error = validate_format_data(data, ["name", "missing"])
        assert is_valid is False
        assert "Required attribute 'missing' is missing" in error
    
    def test_validate_empty_required_fields(self):
        """Test validation with no required fields"""
        data = {"any": "data"}
        is_valid, error = validate_format_data(data, [])
        assert is_valid is True
        assert error is None


class TestFormatDataValidator:
    """Test FormatDataValidator class"""
    
    def test_basic_initialization(self):
        """Test basic validator initialization"""
        validator = FormatDataValidator()
        assert validator.required_fields == []
        assert validator.custom_validators == {}
        
        validator = FormatDataValidator(["field1", "field2"])
        assert validator.required_fields == ["field1", "field2"]
    
    def test_validate_with_required_fields(self):
        """Test validation with required fields"""
        validator = FormatDataValidator(["name", "value"])
        
        # Valid data
        data = {"name": "test", "value": 42}
        is_valid, errors = validator.validate(data)
        assert is_valid is True
        assert errors == []
        
        # Invalid data
        data = {"name": "test"}
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert len(errors) == 1
        assert "Required key 'value' is missing" in errors[0]
    
    def test_custom_validators(self):
        """Test custom validation functions"""
        def validate_positive(value):
            return isinstance(value, (int, float)) and value > 0
        
        def validate_string_length(value):
            return isinstance(value, str) and len(value) >= 3
        
        validator = FormatDataValidator(
            required_fields=["count", "name"],
            custom_validators={
                "count": validate_positive,
                "name": validate_string_length
            }
        )
        
        # Valid data
        data = {"count": 5, "name": "test"}
        is_valid, errors = validator.validate(data)
        assert is_valid is True
        assert errors == []
        
        # Invalid count
        data = {"count": -1, "name": "test"}
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any("Custom validation failed for field 'count'" in error for error in errors)
        
        # Invalid name
        data = {"count": 5, "name": "ab"}
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any("Custom validation failed for field 'name'" in error for error in errors)
    
    def test_custom_validator_exception_handling(self):
        """Test custom validator exception handling"""
        def failing_validator(value):
            raise ValueError("Intentional error")
        
        validator = FormatDataValidator(
            required_fields=["field"],
            custom_validators={"field": failing_validator}
        )
        
        data = {"field": "value"}
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert any("Custom validation error for field 'field'" in error for error in errors)
    
    def test_add_required_field(self):
        """Test adding required fields dynamically"""
        validator = FormatDataValidator()
        
        validator.add_required_field("new_field")
        assert "new_field" in validator.required_fields
        
        # Don't add duplicates
        validator.add_required_field("new_field")
        assert validator.required_fields.count("new_field") == 1
    
    def test_add_custom_validator(self):
        """Test adding custom validators dynamically"""
        validator = FormatDataValidator()
        
        def test_validator(value):
            return value == "test"
        
        validator.add_custom_validator("field", test_validator)
        assert "field" in validator.custom_validators
        assert validator.custom_validators["field"] == test_validator
    
    def test_validate_format_context_success(self):
        """Test successful format context validation"""
        validator = FormatDataValidator(["template", "env"])
        
        context = {"template": "/path/{name}", "env": "docker", "extra": "value"}
        is_valid, errors = validator.validate_format_context(context)
        assert is_valid is True
        assert errors == []
    
    def test_validate_format_context_invalid_type(self):
        """Test format context validation with invalid type"""
        validator = FormatDataValidator()
        
        is_valid, errors = validator.validate_format_context("not a dict")
        assert is_valid is False
        assert "Context must be a dictionary" in errors
    
    def test_validate_format_context_missing_keys(self):
        """Test format context validation with missing keys"""
        validator = FormatDataValidator(["required1", "required2"])
        
        context = {"required1": "value"}
        is_valid, errors = validator.validate_format_context(context)
        assert is_valid is False
        assert "Required context key 'required2' is missing" in errors
    
    def test_validate_format_context_none_values(self):
        """Test format context validation with None values"""
        validator = FormatDataValidator(["key1", "key2"])
        
        context = {"key1": "value", "key2": None}
        is_valid, errors = validator.validate_format_context(context)
        assert is_valid is False
        assert "Context key 'key2' cannot be None" in errors
    
    def test_validate_with_dataclass(self):
        """Test validator with dataclass objects"""
        validator = FormatDataValidator(["name", "value"])
        
        # Valid dataclass
        data = SampleDataClass(name="test", value=42)
        is_valid, errors = validator.validate(data)
        assert is_valid is True
        assert errors == []
        
        # Invalid dataclass
        data = SampleDataClass(name="", value=42)
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert len(errors) > 0
    
    def test_multiple_validation_errors(self):
        """Test handling multiple validation errors"""
        def always_false(value):
            return False
        
        validator = FormatDataValidator(
            required_fields=["missing"],
            custom_validators={"present": always_false}
        )
        
        data = {"present": "value"}
        is_valid, errors = validator.validate(data)
        assert is_valid is False
        assert len(errors) == 2  # One for missing field, one for custom validation


class TestEdgeCases:
    """Test edge cases and boundary conditions"""
    
    def test_empty_validator(self):
        """Test validator with no requirements"""
        validator = FormatDataValidator()
        
        # Should pass with any data
        is_valid, errors = validator.validate({"any": "data"})
        assert is_valid is True
        assert errors == []
        
        is_valid, errors = validator.validate(SampleDataClass("name", 1))
        assert is_valid is True
        assert errors == []
    
    def test_custom_validator_field_not_present(self):
        """Test custom validator when field is not present in data"""
        def test_validator(value):
            return True
        
        validator = FormatDataValidator(
            custom_validators={"non_existent": test_validator}
        )
        
        data = {"other_field": "value"}
        is_valid, errors = validator.validate(data)
        assert is_valid is True  # Should not fail if field is not present
        assert errors == []
    
    def test_validate_complex_nested_data(self):
        """Test validation with complex nested data structures"""
        @dataclass
        class ComplexData:
            nested_dict: Dict[str, Any]
            nested_list: list
        
        data = ComplexData(
            nested_dict={"inner": "value"},
            nested_list=[1, 2, 3]
        )
        
        validator = FormatDataValidator(["nested_dict", "nested_list"])
        is_valid, errors = validator.validate(data)
        assert is_valid is True
        assert errors == []