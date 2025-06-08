"""Tests for ContextValidator"""

from unittest.mock import Mock, patch

import pytest

from src.context.context_validator import ContextValidator


class TestContextValidator:
    """Test cases for ContextValidator"""

    @patch('src.context.context_validator.validate_execution_context_data')
    def test_validate_execution_context_success(self, mock_validate):
        """Test successful execution context validation"""
        # Setup mock execution data
        execution_data = Mock()
        execution_data.command_type = "test"
        execution_data.language = "python"
        execution_data.contest_name = "abc300"
        execution_data.problem_name = "a"
        execution_data.env_json = {"python": {"commands": {}}}

        # Setup mock validation function to return success
        mock_validate.return_value = (True, None)

        # Execute validation
        is_valid, error = ContextValidator.validate_execution_context(execution_data)

        # Verify results
        assert is_valid
        assert error is None

        # Verify the underlying function was called with correct arguments
        mock_validate.assert_called_once_with(
            "test",
            "python",
            "abc300",
            "a",
            {"python": {"commands": {}}}
        )

    @patch('src.context.context_validator.validate_execution_context_data')
    def test_validate_execution_context_failure(self, mock_validate):
        """Test execution context validation failure"""
        # Setup mock execution data
        execution_data = Mock()
        execution_data.command_type = "invalid"
        execution_data.language = "unknown"
        execution_data.contest_name = "abc300"
        execution_data.problem_name = "a"
        execution_data.env_json = {}

        # Setup mock validation function to return failure
        mock_validate.return_value = (False, "Invalid configuration")

        # Execute validation
        is_valid, error = ContextValidator.validate_execution_context(execution_data)

        # Verify results
        assert not is_valid
        assert error == "Invalid configuration"

        # Verify the underlying function was called
        mock_validate.assert_called_once_with(
            "invalid",
            "unknown",
            "abc300",
            "a",
            {}
        )

    def test_validate_required_fields_success(self):
        """Test successful required fields validation"""
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = {
            "python": {"commands": {"test": {}}}
        }

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert is_valid
        assert error is None

    def test_validate_required_fields_no_language(self):
        """Test required fields validation with no language"""
        execution_data = Mock()
        execution_data.language = None
        execution_data.env_json = {"python": {}}

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "言語が指定されていません"

    def test_validate_required_fields_empty_language(self):
        """Test required fields validation with empty language"""
        execution_data = Mock()
        execution_data.language = ""
        execution_data.env_json = {"python": {}}

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "言語が指定されていません"

    def test_validate_required_fields_no_env_json(self):
        """Test required fields validation with no env_json"""
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = None

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "環境設定が見つかりません"

    def test_validate_required_fields_empty_env_json(self):
        """Test required fields validation with empty env_json"""
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = {}

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "環境設定が見つかりません"

    def test_validate_required_fields_language_not_in_env_json(self):
        """Test required fields validation when language not in env_json"""
        execution_data = Mock()
        execution_data.language = "ruby"
        execution_data.env_json = {
            "python": {"commands": {}},
            "cpp": {"commands": {}}
        }

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "言語 'ruby' の設定が見つかりません"

    def test_validate_required_fields_complex_env_json(self):
        """Test required fields validation with complex env_json structure"""
        execution_data = Mock()
        execution_data.language = "cpp"
        execution_data.env_json = {
            "python": {"commands": {"test": {}}},
            "cpp": {
                "commands": {
                    "compile": {"steps": []},
                    "run": {"steps": []}
                }
            },
            "shared": {"config": "value"}
        }

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert is_valid
        assert error is None

    def test_static_methods(self):
        """Test that validator methods are static"""
        # Should be able to call without instantiating the class
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = {"python": {}}

        # This should work without creating an instance
        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert isinstance(is_valid, bool)
        assert error is None or isinstance(error, str)

    @patch('src.context.context_validator.validate_execution_context_data')
    def test_validate_execution_context_with_none_values(self, mock_validate):
        """Test execution context validation with None values"""
        execution_data = Mock()
        execution_data.command_type = None
        execution_data.language = None
        execution_data.contest_name = None
        execution_data.problem_name = None
        execution_data.env_json = None

        mock_validate.return_value = (False, "Missing required data")

        is_valid, error = ContextValidator.validate_execution_context(execution_data)

        assert not is_valid
        assert error == "Missing required data"

        mock_validate.assert_called_once_with(None, None, None, None, None)

    def test_validate_required_fields_language_case_sensitivity(self):
        """Test required fields validation language case sensitivity"""
        execution_data = Mock()
        execution_data.language = "Python"  # Capital P
        execution_data.env_json = {
            "python": {"commands": {}},  # lowercase
            "Python": {"commands": {}}   # uppercase
        }

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert is_valid
        assert error is None

    def test_validate_required_fields_boolean_false_language(self):
        """Test required fields validation with boolean False language"""
        execution_data = Mock()
        execution_data.language = False
        execution_data.env_json = {"python": {}}

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "言語が指定されていません"

    def test_validate_required_fields_zero_language(self):
        """Test required fields validation with zero as language"""
        execution_data = Mock()
        execution_data.language = 0
        execution_data.env_json = {"python": {}}

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "言語が指定されていません"

    def test_validate_required_fields_dict_false_env_json(self):
        """Test required fields validation with dict evaluating to False"""
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = {}  # Empty dict is falsy

        is_valid, error = ContextValidator.validate_required_fields(execution_data)

        assert not is_valid
        assert error == "環境設定が見つかりません"
