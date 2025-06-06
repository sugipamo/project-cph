"""
End-to-end tests for custom format integration
"""
import pytest
from unittest.mock import Mock, MagicMock
from src.operations.formatters.test_result_formatter import (
    TemplateBasedFormatter, AdvancedFormatOptions, TestResult, TestStatus
)
from src.operations.formatters.base_format_engine import FormatSyntaxType
from src.operations.factory.unified_request_factory import ComplexRequestStrategy
from src.env_core.step.step import Step, StepType
from src.operations.environment.environment_manager import EnvironmentManager


class TestTemplateBasedFormatter:
    """Test template-based formatter end-to-end"""
    
    def setup_method(self):
        """Set up formatter"""
        self.formatter = TemplateBasedFormatter()
    
    def test_format_single_pass_result(self):
        """Test formatting single passing test result"""
        result = TestResult(
            test_name="sample-1",
            status=TestStatus.PASS,
            execution_time=0.023
        )
        
        options = AdvancedFormatOptions(
            template_syntax=FormatSyntaxType.PYTHON,
            templates={
                "default": "{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}"
            }
        )
        
        formatted = self.formatter.format_single_result(result, options)
        
        assert "sample-1" in formatted
        assert "✅" in formatted or "PASS" in formatted
        assert "0.023s" in formatted
    
    def test_format_single_fail_result(self):
        """Test formatting single failing test result"""
        result = TestResult(
            test_name="sample-2",
            status=TestStatus.FAIL,
            expected_output="2",
            actual_output="1",
            execution_time=0.041
        )
        
        options = AdvancedFormatOptions(
            templates={
                "fail": "{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}\\n  Expected: {expected_output}\\n  Got:      {actual_output}"
            }
        )
        
        formatted = self.formatter.format_single_result(result, options)
        
        assert "sample-2" in formatted
        assert "❌" in formatted or "FAIL" in formatted
        assert "Expected: 2" in formatted
        assert "Got:      1" in formatted
    
    def test_format_single_error_result(self):
        """Test formatting single error test result"""
        result = TestResult(
            test_name="sample-3",
            status=TestStatus.ERROR,
            error_message="ValueError: invalid input",
            execution_time=0.002
        )
        
        options = AdvancedFormatOptions(
            templates={
                "error": "{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}\\n  Error: {error_message}"
            }
        )
        
        formatted = self.formatter.format_single_result(result, options)
        
        assert "sample-3" in formatted
        assert "💥" in formatted or "ERROR" in formatted
        assert "ValueError: invalid input" in formatted
    
    def test_format_summary(self):
        """Test formatting test summary"""
        results = [
            TestResult("test1", TestStatus.PASS),
            TestResult("test2", TestStatus.PASS),
            TestResult("test3", TestStatus.FAIL),
        ]
        
        options = AdvancedFormatOptions(
            templates={
                "summary": "Tests: {passed:03d}/{total:03d} passed ({pass_rate:.1f}%)"
            }
        )
        
        summary = self.formatter.format_summary(results, options)
        
        assert "002/003 passed" in summary
        assert "66.7%" in summary
    
    def test_advanced_format_specifications(self):
        """Test advanced Python format specifications"""
        result = TestResult(
            test_name="long-test-name",
            status=TestStatus.PASS,
            execution_time=0.123456
        )
        
        options = AdvancedFormatOptions(
            templates={
                "default": "{test_name:>30} | {status:^10} | {time_ms:>5d}ms | {execution_time:>8.3f}s"
            }
        )
        
        formatted = self.formatter.format_single_result(result, options)
        
        assert "long-test-name" in formatted
        assert "123ms" in formatted
        assert "0.123s" in formatted
    
    def test_format_error_handling(self):
        """Test error handling in formatting"""
        result = TestResult("test", TestStatus.PASS)
        
        # Invalid template
        options = AdvancedFormatOptions(
            strict_formatting=True,
            templates={
                "default": "{nonexistent_key}"
            }
        )
        
        formatted = self.formatter.format_single_result(result, options)
        
        # Should fallback to error message
        assert "[Format Error]" in formatted
        assert "test" in formatted
        assert "PASS" in formatted


class TestUnifiedRequestFactoryIntegration:
    """Test integration with unified request factory"""
    
    def setup_method(self):
        """Set up strategy"""
        self.strategy = ComplexRequestStrategy()
        self.env_manager = Mock(spec=EnvironmentManager)
        self.env_manager.get_timeout.return_value = 30
        self.env_manager.get_working_directory.return_value = "/test/dir"
    
    def test_default_test_script_generation(self):
        """Test default test script generation"""
        step = Mock(spec=Step)
        step.type = StepType.TEST
        step.cmd = ["python3", "main.py"]
        step.cwd = None
        step.env = None
        step.allow_failure = False
        
        # No format options - should use default
        context = Mock()
        context.format_string = Mock(side_effect=lambda x: x.replace("{contest_current_path}", "./contest_current"))
        
        request = self.strategy.create_request(step, context, self.env_manager)
        
        assert request is not None
        assert "bash" in request.cmd
        assert "✓ PASS" in request.cmd[2]
        assert "✗ FAIL" in request.cmd[2]
    
    def test_template_test_script_generation(self):
        """Test template-based test script generation"""
        step = Mock(spec=Step)
        step.type = StepType.TEST
        step.cmd = ["python3", "main.py"]
        step.cwd = None
        step.env = None
        step.allow_failure = False
        step.output_format = "template"
        step.format_options = {
            "templates": {
                "default": "{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}"
            }
        }
        
        context = Mock()
        context.format_string = Mock(side_effect=lambda x: x.replace("{contest_current_path}", "./contest_current"))
        
        request = self.strategy.create_request(step, context, self.env_manager)
        
        assert request is not None
        assert "bash" in request.cmd
        # Should use template-based formatting
        assert "printf" in request.cmd[2]
        assert "✅" in request.cmd[2]
        assert "❌" in request.cmd[2]
    
    def test_create_default_test_script(self):
        """Test default test script creation method"""
        script = self.strategy._create_default_test_script(
            "./contest_current",
            ["python3", "main.py"]
        )
        
        assert "for i in ./contest_current/test/sample-*.in" in script
        assert "python3 main.py" in script
        assert "✓ PASS" in script
        assert "✗ FAIL" in script
        assert "✗ ERROR" in script
    
    def test_create_template_test_script(self):
        """Test template test script creation method"""
        format_options = {
            "templates": {
                "default": "{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}",
                "summary": "Tests: {passed:03d}/{total:03d} passed ({pass_rate:.1f}%)"
            }
        }
        
        script = self.strategy._create_template_test_script(
            "./contest_current",
            ["python3", "main.py"],
            format_options
        )
        
        assert "for i in ./contest_current/test/sample-*.in" in script
        assert "python3 main.py" in script
        assert "printf" in script
        assert "total_tests" in script
        assert "passed_tests" in script


class TestFullWorkflow:
    """Test full workflow integration"""
    
    def test_env_json_to_formatted_output(self):
        """Test complete workflow from env.json to formatted output"""
        # Simulate env.json configuration
        env_config = {
            "python": {
                "commands": {
                    "test": {
                        "steps": [{
                            "type": "test",
                            "cmd": ["python3", "{source_file_name}"],
                            "output_format": "template",
                            "format_options": {
                                "template_syntax": "python",
                                "strict_formatting": True,
                                "templates": {
                                    "default": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}",
                                    "fail": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}\\n    Expected: {expected_output}\\n    Got:      {actual_output}",
                                    "summary": "Results: {passed:03d}/{total:03d} tests passed"
                                }
                            }
                        }]
                    }
                }
            }
        }
        
        # This would normally be parsed by the system
        step_config = env_config["python"]["commands"]["test"]["steps"][0]
        
        # Verify configuration structure
        assert step_config["output_format"] == "template"
        assert step_config["format_options"]["template_syntax"] == "python"
        assert "default" in step_config["format_options"]["templates"]
        
        # Test that the templates contain expected elements
        default_template = step_config["format_options"]["templates"]["default"]
        assert "{test_name" in default_template
        assert "{status_symbol}" in default_template
        assert "{time_formatted" in default_template
    
    def test_formatter_with_real_templates(self):
        """Test formatter with realistic templates"""
        formatter = TemplateBasedFormatter()
        
        # Test results
        results = [
            TestResult("sample-1.in", TestStatus.PASS, execution_time=0.023),
            TestResult("sample-2.in", TestStatus.FAIL, 
                      expected_output="2", actual_output="1", execution_time=0.041),
            TestResult("sample-long-name.in", TestStatus.ERROR, 
                      error_message="ValueError: invalid input", execution_time=0.002)
        ]
        
        # Realistic format options
        options = AdvancedFormatOptions(
            template_syntax=FormatSyntaxType.PYTHON,
            strict_formatting=True,
            templates={
                "default": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}",
                "fail": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}\\n    Expected: {expected_output}\\n    Got:      {actual_output}",
                "error": "{test_name:.<30} │ {status_symbol} {status:^10} │ {time_formatted:>12}\\n    Error: {error_message}",
                "summary": "Results: {passed:03d}/{total:03d} tests passed"
            }
        )
        
        # Format each result
        for result in results:
            formatted = formatter.format_single_result(result, options)
            assert len(formatted) > 0
            assert result.test_name in formatted
            
        # Format summary
        summary = formatter.format_summary(results, options)
        assert "001/003" in summary
        assert "Results:" in summary