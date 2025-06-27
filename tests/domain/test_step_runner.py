"""Tests for step_runner module - step execution and template expansion"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from src.domain.step_runner import (
    expand_template,
    evaluate_test_condition,
    expand_step_with_file_patterns,
    create_step,
    expand_when_condition,
    ExecutionContext,
    _contains_template_variables
)


class TestStepRunner:
    """Test suite for step runner functionality"""
    
    def setup_method(self):
        """Set up test fixtures"""
        self.mock_os_provider = Mock()
        self.mock_json_provider = Mock()
        self.execution_context = ExecutionContext(
            contest_name="ABC100",
            problem_name="A",
            language="python",
            local_workspace_path="/workspace",
            contest_current_path="/contest/current",
            contest_stock_path="/contest/stock",
            contest_template_path="/contest/template",
            source_file_name="main.py",
            language_id="py"
        )
    
    def test_contains_template_variables(self):
        """Test detection of template variables"""
        assert _contains_template_variables("Hello {name}!") is True
        assert _contains_template_variables("No templates here") is False
        assert _contains_template_variables("{var1} and {var2}") is True
        assert _contains_template_variables("") is False
    
    def test_expand_template_with_execution_context(self):
        """Test template expansion with ExecutionContext"""
        template = "Contest: {contest_name}, Problem: {problem_name}"
        
        result = expand_template(template, self.execution_context)
        
        assert result == "Contest: ABC100, Problem: A"
    
    def test_expand_template_with_dict_context(self):
        """Test template expansion with dictionary context"""
        template = "{greeting} {name}!"
        context = Mock()
        context.to_dict.return_value = {"greeting": "Hello", "name": "World"}
        
        result = expand_template(template, context)
        
        assert result == "Hello World!"
    
    def test_expand_template_empty_string(self):
        """Test template expansion with empty string"""
        result = expand_template("", self.execution_context)
        assert result == ""
    
    def test_expand_template_no_variables(self):
        """Test template expansion with no variables"""
        template = "Just plain text"
        result = expand_template(template, self.execution_context)
        assert result == "Just plain text"
    
    def test_evaluate_test_condition_directory_exists(self):
        """Test evaluation of directory existence condition"""
        self.mock_os_provider.isdir.return_value = True
        
        result, error = evaluate_test_condition("test -d /some/path", self.mock_os_provider)
        
        assert result is True
        assert error is None
        self.mock_os_provider.isdir.assert_called_once_with("/some/path")
    
    def test_evaluate_test_condition_file_exists(self):
        """Test evaluation of file existence condition"""
        self.mock_os_provider.isfile.return_value = True
        
        result, error = evaluate_test_condition("-f /some/file.txt", self.mock_os_provider)
        
        assert result is True
        assert error is None
        self.mock_os_provider.isfile.assert_called_once_with("/some/file.txt")
    
    def test_evaluate_test_condition_path_exists(self):
        """Test evaluation of path existence condition"""
        self.mock_os_provider.path_exists.return_value = False
        
        result, error = evaluate_test_condition("test -e /nonexistent", self.mock_os_provider)
        
        assert result is False
        assert error is None
        self.mock_os_provider.path_exists.assert_called_once_with("/nonexistent")
    
    def test_evaluate_test_condition_negation(self):
        """Test evaluation of negated condition"""
        self.mock_os_provider.isdir.return_value = False
        
        result, error = evaluate_test_condition("test ! -d /not/a/dir", self.mock_os_provider)
        
        assert result is True
        assert error is None
        self.mock_os_provider.isdir.assert_called_once_with("/not/a/dir")
    
    def test_evaluate_test_condition_empty(self):
        """Test evaluation of empty condition"""
        result, error = evaluate_test_condition("", self.mock_os_provider)
        
        assert result is True
        assert error is None
    
    def test_evaluate_test_condition_invalid(self):
        """Test evaluation of invalid condition"""
        result, error = evaluate_test_condition("invalid condition", self.mock_os_provider)
        
        assert result is False
        assert "test条件は 'test' で始まる必要があります" in error
    
    def test_expand_when_condition_true(self):
        """Test when condition expansion and evaluation"""
        self.mock_os_provider.isdir.return_value = True
        
        result, error = expand_when_condition(
            "test -d {contest_current_path}", 
            self.execution_context,
            self.mock_os_provider
        )
        
        assert result is True
        assert error is None
        self.mock_os_provider.isdir.assert_called_once_with("/contest/current")
    
    def test_expand_when_condition_false(self):
        """Test when condition that evaluates to false"""
        self.mock_os_provider.isfile.return_value = False
        
        result, error = expand_when_condition(
            "test -f {source_file_name}",
            self.execution_context,
            self.mock_os_provider
        )
        
        assert result is False
        assert error is None
    
    def test_expand_step_with_file_patterns_no_patterns(self):
        """Test step expansion when no file patterns present"""
        json_step = {
            "name": "simple_step",
            "cmd": "echo 'hello'"
        }
        
        result = expand_step_with_file_patterns(
            json_step, 
            self.execution_context,
            self.mock_json_provider,
            self.mock_os_provider
        )
        
        assert len(result) == 1
        assert result[0] == json_step
    
    def test_expand_step_with_file_patterns_contest_files(self):
        """Test step expansion with contest_files pattern"""
        json_step = {
            "name": "process_files",
            "cmd": "process {contest_files}"
        }
        
        # Mock file pattern resolution
        with patch('src.domain.step_runner.get_file_patterns_from_context') as mock_get_patterns:
            mock_get_patterns.return_value = ["*.in", "*.txt"]
            
            with patch('src.domain.step_runner.expand_file_patterns_to_files') as mock_expand:
                mock_expand.return_value = ["test1.in", "test2.txt"]
                
                result = expand_step_with_file_patterns(
                    json_step,
                    self.execution_context,
                    self.mock_json_provider,
                    self.mock_os_provider
                )
        
        assert len(result) == 2
        assert result[0]["cmd"] == "process test1.in"
        assert result[1]["cmd"] == "process test2.txt"
    
    @patch('src.domain.step_runner.StepType')
    def test_create_step_basic(self, mock_step_type):
        """Test basic step creation"""
        json_step = {
            "name": "test_step",
            "type": "python",
            "cmd": ["python", "main.py"]
        }
        
        mock_step_type.PYTHON = "python"
        
        with patch('src.domain.step_runner.Step') as mock_step_class:
            mock_step = Mock()
            mock_step_class.return_value = mock_step
            
            result = create_step(
                json_step,
                self.execution_context,
                self.mock_json_provider,
                self.mock_os_provider
            )
            
            assert result == mock_step
            mock_step_class.assert_called_once()
    
    @patch('src.domain.step_runner.expand_when_condition')
    def test_create_step_with_when_condition_false(self, mock_expand_when):
        """Test step creation when 'when' condition is false"""
        json_step = {
            "name": "conditional_step",
            "type": "shell",
            "cmd": "echo 'should not run'",
            "when": "test -d /nonexistent"
        }
        
        mock_expand_when.return_value = (False, None)
        
        result = create_step(
            json_step,
            self.execution_context,
            self.mock_json_provider,
            self.mock_os_provider
        )
        
        assert result is None
    
    def test_execution_context_to_dict(self):
        """Test ExecutionContext conversion to dictionary"""
        context_dict = self.execution_context.to_dict()
        
        assert context_dict["contest_name"] == "ABC100"
        assert context_dict["problem_name"] == "A"
        assert context_dict["language"] == "python"
        assert context_dict["language_name"] == "python"  # Alias for backward compatibility
        assert context_dict["local_workspace_path"] == "/workspace"