"""
Unified configuration management system for CPH project
"""
from .manager import ConfigurationManager, UnifiedConfig
from .validation import UnifiedConfigValidator, ConfigValidationResult
from .exceptions import ConfigurationError, ConfigValidationError, ConfigResolutionError
from .schema import ConfigSchemaValidator
from .template import TemplateProcessor
from .discovery import ConfigDiscovery
from .cache import ConfigCache