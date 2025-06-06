"""
Python Format Engine - Python str.format() / f-string syntax support
"""
import re
import string
from typing import Dict, Any, List, Set
from src.context.utils.format_utils import format_with_missing_keys, extract_format_keys
from .base_format_engine import FormatEngine, FormatContext, FormatResult, FormatSyntaxType


class PythonFormatEngine(FormatEngine):
    """Python str.format() / f-string syntax engine"""
    
    # Advanced Python format specification detection patterns
    PYTHON_FORMAT_PATTERN = re.compile(
        r'\{[^}]*:[^}]*\}|'      # {name:format_spec}
        r'\{[^}]*\![^}]*\}|'     # {name!conversion}
        r'\{[0-9]+\}'            # {0}, {1} (positional)
    )
    
    @property
    def syntax_type(self) -> FormatSyntaxType:
        return FormatSyntaxType.PYTHON
    
    @property
    def name(self) -> str:
        return "python_format"
    
    def supports_syntax(self, template: str) -> bool:
        """Detect Python format syntax"""
        # Basic {key} format
        if extract_format_keys(template):
            return True
        
        # Advanced format specifications: {name:format_spec}, {name!conversion}
        return bool(self.PYTHON_FORMAT_PATTERN.search(template))
    
    def format(self, template: str, context: FormatContext) -> FormatResult:
        """Format with Python format syntax"""
        try:
            if self._has_advanced_format_spec(template):
                # Advanced format specification processing
                return self._format_advanced(template, context)
            else:
                # Leverage existing basic processing
                return self._format_basic(template, context)
        
        except Exception as e:
            return FormatResult(
                formatted_text=template,
                success=False,
                error_message=str(e)
            )
    
    def _has_advanced_format_spec(self, template: str) -> bool:
        """Check if advanced format specification is included"""
        return bool(self.PYTHON_FORMAT_PATTERN.search(template))
    
    def _format_basic(self, template: str, context: FormatContext) -> FormatResult:
        """Basic format processing (leverage existing functionality)"""
        try:
            formatted, missing = format_with_missing_keys(template, **context.data)
            
            if missing and context.strict_mode:
                return FormatResult(
                    formatted_text=formatted,
                    success=False,
                    missing_keys=missing,
                    error_message=f"Missing keys: {missing}"
                )
            
            return FormatResult(formatted_text=formatted, missing_keys=missing)
        
        except Exception as e:
            return FormatResult(
                formatted_text=template,
                success=False,
                error_message=str(e)
            )
    
    def _format_advanced(self, template: str, context: FormatContext) -> FormatResult:
        """Advanced format specification processing"""
        try:
            # Use Python's built-in str.format()
            formatted = template.format(**context.data)
            return FormatResult(formatted_text=formatted)
        
        except KeyError as e:
            missing_key = str(e).strip("'\"")
            if context.strict_mode:
                return FormatResult(
                    formatted_text=template,
                    success=False,
                    missing_keys=[missing_key],
                    error_message=f"Missing key: {missing_key}"
                )
            else:
                # Fallback processing
                safe_data = self._create_safe_data(context.data, template)
                try:
                    formatted = template.format(**safe_data)
                    return FormatResult(
                        formatted_text=formatted,
                        missing_keys=[missing_key]
                    )
                except Exception:
                    return FormatResult(
                        formatted_text=template,
                        success=False,
                        missing_keys=[missing_key],
                        error_message=str(e)
                    )
        
        except (ValueError, TypeError) as e:
            return FormatResult(
                formatted_text=template,
                success=False,
                error_message=f"Format error: {e}"
            )
    
    def _create_safe_data(self, data: Dict[str, Any], template: str) -> Dict[str, Any]:
        """Create safe data dictionary (missing key support)"""
        safe_data = data.copy()
        
        # Extract required keys from template
        required_keys = self._extract_all_format_keys(template)
        
        # Set fallback values for missing keys
        for key in required_keys:
            if key not in safe_data:
                safe_data[key] = ""  # Fallback with empty string
        
        return safe_data
    
    def _extract_all_format_keys(self, template: str) -> Set[str]:
        """Extract all keys from template"""
        keys = set()
        
        # Basic {key} format - filter out positional arguments
        basic_keys = extract_format_keys(template)
        keys.update(key for key in basic_keys if not key.isdigit())
        
        # Extract from advanced format specifications
        for match in self.PYTHON_FORMAT_PATTERN.finditer(template):
            spec = match.group(0)
            # Extract name from {name:format} or {name!conversion}
            if ':' in spec:
                key = spec[1:].split(':')[0]
            elif '!' in spec:
                key = spec[1:].split('!')[0]
            else:
                key = spec[1:-1]
            
            if key and not key.isdigit():  # Not positional argument
                keys.add(key)
        
        return keys


class EnhancedPythonFormatEngine(PythonFormatEngine):
    """Enhanced Python format engine (for future advanced features)"""
    
    @property
    def name(self) -> str:
        return "enhanced_python_format"
    
    def _format_advanced(self, template: str, context: FormatContext) -> FormatResult:
        """Extended advanced format processing"""
        # Apply custom formatters
        if context.extra_options and 'custom_formatters' in context.extra_options:
            return self._apply_custom_formatters(template, context)
        
        # Basic processing
        return super()._format_advanced(template, context)
    
    def _apply_custom_formatters(self, template: str, context: FormatContext) -> FormatResult:
        """Apply custom formatters"""
        # Future implementation: custom format specification processing
        # Example: {time:ms} → millisecond display, {size:human} → human readable size
        return super()._format_advanced(template, context)