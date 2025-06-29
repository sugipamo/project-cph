"""Tests for context validator."""
import pytest
from unittest.mock import Mock, patch
from src.presentation.context_validator import ContextValidator


class TestContextValidator:
    """Test cases for ContextValidator class."""

    @patch('src.presentation.context_validator.validate_execution_context_data')
    def test_validate_execution_context_success(self, mock_validate):
        """Test successful execution context validation."""
        # Mock validation function
        mock_validate.return_value = (True, None)
        
        # Create mock execution data
        execution_data = Mock()
        execution_data.command_type = "test"
        execution_data.language = "python"
        execution_data.contest_name = "contest1"
        execution_data.problem_name = "problem1"
        execution_data.env_json = {"python": {"version": "3.8"}}
        
        # Validate
        result, error = ContextValidator.validate_execution_context(execution_data)
        
        assert result is True
        assert error is None
        mock_validate.assert_called_once_with(
            "test",
            "python",
            "contest1",
            "problem1",
            {"python": {"version": "3.8"}}
        )

    @patch('src.presentation.context_validator.validate_execution_context_data')
    def test_validate_execution_context_failure(self, mock_validate):
        """Test failed execution context validation."""
        # Mock validation function
        mock_validate.return_value = (False, "Invalid command type")
        
        # Create mock execution data
        execution_data = Mock()
        execution_data.command_type = "invalid"
        execution_data.language = "python"
        execution_data.contest_name = "contest1"
        execution_data.problem_name = "problem1"
        execution_data.env_json = {"python": {"version": "3.8"}}
        
        # Validate
        result, error = ContextValidator.validate_execution_context(execution_data)
        
        assert result is False
        assert error == "Invalid command type"

    def test_validate_required_fields_success(self):
        """Test successful required fields validation."""
        # Create mock execution data with all required fields
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = {"python": {"version": "3.8"}}
        
        # Validate
        result, error = ContextValidator.validate_required_fields(execution_data)
        
        assert result is True
        assert error is None

    def test_validate_required_fields_no_language(self):
        """Test validation failure when language is missing."""
        # Create mock execution data without language
        execution_data = Mock()
        execution_data.language = None
        execution_data.env_json = {"python": {"version": "3.8"}}
        
        # Validate
        result, error = ContextValidator.validate_required_fields(execution_data)
        
        assert result is False
        assert error == "言語が指定されていません"

    def test_validate_required_fields_empty_language(self):
        """Test validation failure when language is empty string."""
        # Create mock execution data with empty language
        execution_data = Mock()
        execution_data.language = ""
        execution_data.env_json = {"python": {"version": "3.8"}}
        
        # Validate
        result, error = ContextValidator.validate_required_fields(execution_data)
        
        assert result is False
        assert error == "言語が指定されていません"

    def test_validate_required_fields_no_env_json(self):
        """Test validation failure when env_json is missing."""
        # Create mock execution data without env_json
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = None
        
        # Validate
        result, error = ContextValidator.validate_required_fields(execution_data)
        
        assert result is False
        assert error == "環境設定が見つかりません"

    def test_validate_required_fields_empty_env_json(self):
        """Test validation failure when env_json is empty dict."""
        # Create mock execution data with empty env_json
        execution_data = Mock()
        execution_data.language = "python"
        execution_data.env_json = {}
        
        # Validate
        result, error = ContextValidator.validate_required_fields(execution_data)
        
        assert result is False
        assert error == "環境設定が見つかりません"

    def test_validate_required_fields_language_not_in_env(self):
        """Test validation failure when language is not in env_json."""
        # Create mock execution data with mismatched language
        execution_data = Mock()
        execution_data.language = "rust"
        execution_data.env_json = {"python": {"version": "3.8"}, "cpp": {"version": "17"}}
        
        # Validate
        result, error = ContextValidator.validate_required_fields(execution_data)
        
        assert result is False
        assert error == "言語 'rust' の設定が見つかりません"

    def test_validate_required_fields_case_sensitive(self):
        """Test that language validation is case sensitive."""
        # Create mock execution data with different case
        execution_data = Mock()
        execution_data.language = "Python"  # Capital P
        execution_data.env_json = {"python": {"version": "3.8"}}  # lowercase p
        
        # Validate
        result, error = ContextValidator.validate_required_fields(execution_data)
        
        assert result is False
        assert error == "言語 'Python' の設定が見つかりません"