"""
Test Result Formatter - Template-based test result formatting
"""
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from src.application.formatters.base.base_format_engine import FormatSyntaxType
from src.application.formatters.format_manager import get_format_manager
from src.domain.types.execution_types import ExecutionStatus, ExecutionResult

# Aliases for backward compatibility
TestStatus = ExecutionStatus
TestResult = ExecutionResult


@dataclass(frozen=True)
class FormatOptions:
    """Basic format options"""
    show_details: bool = True
    show_timing: bool = True
    max_output_length: int = 200


@dataclass(frozen=True)
class AdvancedFormatOptions(FormatOptions):
    """Advanced format options"""
    # Python format syntax related
    template_syntax: FormatSyntaxType = FormatSyntaxType.PYTHON
    strict_formatting: bool = True
    custom_formatters: Optional[Dict[str, str]] = None
    
    # Template definitions
    templates: Optional[Dict[str, str]] = None


class TestResultFormatter:
    """Base test result formatter"""
    
    @property
    def name(self) -> str:
        return "base"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type == "basic"
    
    def format_single_result(self, result: ExecutionResult, options: FormatOptions) -> str:
        """Format single test result"""
        return f"{result.test_name}: {result.status.value}"
    
    def format_summary(self, results: List[ExecutionResult], options: FormatOptions) -> str:
        """Format test summary"""
        total = len(results)
        passed = len([r for r in results if r.status == ExecutionStatus.PASS])
        return f"Tests: {passed}/{total} passed"


class TemplateBasedFormatter(TestResultFormatter):
    """Template-based test result formatter"""
    
    def __init__(self, default_templates: Optional[Dict[str, str]] = None):
        self.format_manager = get_format_manager()
        self.default_templates = default_templates or self._get_default_templates()
    
    @property
    def name(self) -> str:
        return "template_based"
    
    def supports_format(self, format_type: str) -> bool:
        return format_type in ["template", "python_format", "advanced"]
    
    def format_single_result(self, result: ExecutionResult, options: AdvancedFormatOptions) -> str:
        # Select template
        template = self._select_template(result, options)
        
        # Prepare data
        format_data = self._prepare_format_data(result, options)
        
        # Execute formatting
        format_result = self.format_manager.format(
            template=template,
            data=format_data,
            syntax_type=options.template_syntax,
            strict_mode=options.strict_formatting
        )
        
        if not format_result.success and options.strict_formatting:
            # Fallback on error
            return f"[Format Error] {result.test_name}: {result.status.value}"
        
        return format_result.formatted_text
    
    def format_summary(self, results: List[ExecutionResult], options: AdvancedFormatOptions) -> str:
        """Format test summary with template"""
        templates = options.templates or self.default_templates
        summary_template = templates.get('summary', 'Tests: {passed:03d}/{total:03d} passed ({pass_rate:.1f}%)')
        
        total = len(results)
        passed = len([r for r in results if r.status == ExecutionStatus.PASS])
        pass_rate = (passed / total * 100) if total > 0 else 0
        
        format_data = {
            'total': total,
            'passed': passed,
            'failed': total - passed,
            'pass_rate': pass_rate
        }
        
        format_result = self.format_manager.format(
            template=summary_template,
            data=format_data,
            syntax_type=options.template_syntax,
            strict_mode=options.strict_formatting
        )
        
        return format_result.formatted_text
    
    def _select_template(self, result: ExecutionResult, options: AdvancedFormatOptions) -> str:
        """Select template based on result"""
        templates = options.templates or self.default_templates
        
        # Status-specific template
        status_key = result.status.value.lower()
        if status_key in templates:
            return templates[status_key]
        
        # Default template
        return templates.get('default', '{test_name} | {status}')
    
    def _prepare_format_data(self, result: ExecutionResult, options: AdvancedFormatOptions) -> Dict[str, Any]:
        """Prepare data for formatting"""
        data = {
            'test_name': result.test_name,
            'status': result.status.value,
            'status_upper': result.status.value.upper(),
            'status_symbol': self._get_status_symbol(result.status),
            'expected_output': result.expected_output or '',
            'actual_output': result.actual_output or '',
            'error_message': result.error_message or '',
            'execution_time': result.execution_time or 0.0,
            'time_ms': int((result.execution_time or 0) * 1000),
            'time_formatted': f"{result.execution_time:.3f}s" if result.execution_time else "-",
        }
        
        # Apply custom formatters
        if options.custom_formatters:
            data.update(options.custom_formatters)
        
        return data
    
    def _get_status_symbol(self, status: ExecutionStatus) -> str:
        """Get status symbol"""
        symbols = {
            ExecutionStatus.PASS: "✅",
            ExecutionStatus.FAIL: "❌",
            ExecutionStatus.ERROR: "💥",
            ExecutionStatus.SKIP: "⏭️"
        }
        return symbols.get(status, "❓")
    
    def _get_default_templates(self) -> Dict[str, str]:
        """Default template definitions"""
        return {
            'default': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}',
            'pass': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}',
            'fail': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}\\n  Expected: {expected_output}\\n  Got:      {actual_output}',
            'error': '{test_name:.<25} | {status_symbol} {status:^8} | {time_formatted:>10}\\n  Error: {error_message}',
            'summary': 'Tests: {passed:03d}/{total:03d} passed ({pass_rate:.1f}%)'
        }