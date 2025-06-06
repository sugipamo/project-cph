"""
Format Manager - Unified management of format engines
"""
from typing import Dict, List, Optional
from .base_format_engine import FormatEngine, FormatContext, FormatResult, FormatSyntaxType
from .python_format_engine import PythonFormatEngine, EnhancedPythonFormatEngine


class FormatManager:
    """Unified management of format engines"""
    
    def __init__(self):
        self._engines: Dict[FormatSyntaxType, FormatEngine] = {}
        self._default_engine: Optional[FormatEngine] = None
        self._register_default_engines()
    
    def _register_default_engines(self):
        """Register default engines"""
        # Python format engine
        python_engine = PythonFormatEngine()
        self.register_engine(python_engine)
        
        # Enhanced Python format engine
        enhanced_engine = EnhancedPythonFormatEngine()
        self.register_engine(enhanced_engine, is_default=True)
    
    def register_engine(self, engine: FormatEngine, is_default: bool = False):
        """Register new engine"""
        self._engines[engine.syntax_type] = engine
        if is_default:
            self._default_engine = engine
    
    def format(self, template: str, data: Dict[str, any], 
              syntax_type: Optional[FormatSyntaxType] = None,
              strict_mode: bool = True,
              **extra_options) -> FormatResult:
        """Unified format processing"""
        
        # Create context
        context = FormatContext(
            data=data,
            syntax_type=syntax_type or FormatSyntaxType.PYTHON,
            strict_mode=strict_mode,
            extra_options=extra_options if extra_options else None
        )
        
        # Select engine
        if syntax_type and syntax_type in self._engines:
            engine = self._engines[syntax_type]
        else:
            # Auto detection
            engine = self._detect_engine(template)
        
        return engine.format(template, context)
    
    def _detect_engine(self, template: str) -> FormatEngine:
        """Auto-detect suitable engine for template"""
        for engine in self._engines.values():
            if engine.supports_syntax(template):
                return engine
        
        # Fallback: default engine
        return self._default_engine or list(self._engines.values())[0]
    
    def get_supported_syntax_types(self) -> List[FormatSyntaxType]:
        """List of supported syntax types"""
        return list(self._engines.keys())
    
    def is_syntax_supported(self, syntax_type: FormatSyntaxType) -> bool:
        """Check if specified syntax is supported"""
        return syntax_type in self._engines


# Global instance (singleton-like usage)
_format_manager = FormatManager()


def get_format_manager() -> FormatManager:
    """Get global instance of format manager"""
    return _format_manager


# Convenience functions
def format_template(template: str, data: Dict[str, any], **kwargs) -> FormatResult:
    """Simple format processing function"""
    return _format_manager.format(template, data, **kwargs)