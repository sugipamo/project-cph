"""
Base format engine - Abstract foundation for pluggable formatters
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from enum import Enum


class FormatSyntaxType(Enum):
    """Supported format syntax types"""
    PYTHON = "python"          # Current implementation: Python str.format()
    PRINTF = "printf"          # Future extension: printf style
    JINJA2 = "jinja2"         # Future extension: Jinja2
    TEMPLATE = "template"     # Future extension: Custom template


@dataclass(frozen=True)
class FormatContext:
    """Format processing context (immutable)"""
    data: Dict[str, Any]
    syntax_type: FormatSyntaxType = FormatSyntaxType.PYTHON
    strict_mode: bool = True
    fallback_value: str = ""
    extra_options: Optional[Dict[str, Any]] = None


class FormatResult:
    """Format result with success/failure information"""
    
    def __init__(self, formatted_text: str, success: bool = True, 
                 missing_keys: Optional[List[str]] = None, 
                 error_message: Optional[str] = None):
        self.formatted_text = formatted_text
        self.success = success
        self.missing_keys = missing_keys or []
        self.error_message = error_message
    
    def __str__(self) -> str:
        return self.formatted_text
    
    @property
    def is_success(self) -> bool:
        return self.success
    
    def __repr__(self) -> str:
        return f"FormatResult(success={self.success}, text='{self.formatted_text[:50]}{'...' if len(self.formatted_text) > 50 else ''}')"


class FormatEngine(ABC):
    """Abstract base class for format engines"""
    
    @abstractmethod
    def supports_syntax(self, template: str) -> bool:
        """Check if this syntax is supported"""
        pass
    
    @abstractmethod
    def format(self, template: str, context: FormatContext) -> FormatResult:
        """Format template with context"""
        pass
    
    @property
    @abstractmethod
    def syntax_type(self) -> FormatSyntaxType:
        """Supported syntax type"""
        pass
    
    @property
    @abstractmethod
    def name(self) -> str:
        """Engine name"""
        pass