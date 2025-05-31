"""
Infrastructure package - external concerns and cross-cutting functionality
"""

# Configuration management
try:
    from ..config import (
        ConfigurationManager, UnifiedConfig, ConfigDiscovery,
        ConfigSchemaValidator, TemplateProcessor, ConfigCache
    )
    config_exports = [
        'ConfigurationManager', 'UnifiedConfig', 'ConfigDiscovery',
        'ConfigSchemaValidator', 'TemplateProcessor', 'ConfigCache'
    ]
except ImportError:
    config_exports = []

# Validation services  
try:
    from ..context.utils import ValidationUtils
    from ..utils import validation
    validation_exports = ['ValidationUtils']
except ImportError:
    validation_exports = []

# Utility functions
try:
    from ..utils import formatting
    from ..operations.utils import path_utils, process_utils, pure_functions
    utils_exports = ['formatting', 'path_utils', 'process_utils', 'pure_functions']
except ImportError:
    utils_exports = []

__all__ = config_exports + validation_exports + utils_exports