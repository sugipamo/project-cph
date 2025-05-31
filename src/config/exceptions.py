"""
Configuration management exceptions
"""
from typing import List, Optional, Dict, Any
from ..core.exceptions import CPHException


class ConfigurationError(CPHException):
    """Base configuration error"""
    
    def __init__(self, message: str, config_file: Optional[str] = None,
                 config_path: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.config_file = config_file
        self.config_path = config_path
        
        full_message = message
        if config_file:
            full_message += f" (file: {config_file})"
        if config_path:
            path_str = ".".join(config_path)
            full_message += f" (path: {path_str})"
        
        config_context = context or {}
        if config_file:
            config_context['config_file'] = config_file
        if config_path:
            config_context['config_path'] = config_path
        
        super().__init__(full_message, config_context)


class ConfigValidationError(ConfigurationError):
    """Configuration validation failed"""
    
    def __init__(self, field: str, reason: str, value: Any = None,
                 config_file: Optional[str] = None,
                 schema_path: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.field = field
        self.reason = reason
        self.value = value
        self.schema_path = schema_path
        
        message = f"Configuration validation failed for '{field}': {reason}"
        if value is not None:
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:97] + "..."
            message += f" (value: {value_str})"
        
        validation_context = context or {}
        validation_context.update({
            'field': field,
            'reason': reason,
            'value': value
        })
        if schema_path:
            validation_context['schema_path'] = schema_path
        
        super().__init__(message, config_file, schema_path, validation_context)


class ConfigResolutionError(ConfigurationError):
    """Configuration path resolution failed"""
    
    def __init__(self, path: List[str], reason: str,
                 config_file: Optional[str] = None,
                 available_keys: Optional[List[str]] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.path = path
        self.reason = reason
        self.available_keys = available_keys
        
        path_str = ".".join(path)
        message = f"Configuration resolution failed for path '{path_str}': {reason}"
        
        if available_keys:
            message += f" (available: {', '.join(available_keys)})"
        
        resolution_context = context or {}
        resolution_context.update({
            'resolution_path': path,
            'reason': reason
        })
        if available_keys:
            resolution_context['available_keys'] = available_keys
        
        super().__init__(message, config_file, path, resolution_context)


class ConfigTemplateError(ConfigurationError):
    """Configuration template processing failed"""
    
    def __init__(self, template: str, missing_variables: List[str],
                 config_file: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.template = template
        self.missing_variables = missing_variables
        
        message = f"Template processing failed: missing variables {missing_variables}"
        if len(template) <= 100:
            message += f" (template: {template})"
        
        template_context = context or {}
        template_context.update({
            'template': template,
            'missing_variables': missing_variables
        })
        
        super().__init__(message, config_file, None, template_context)


class ConfigSchemaError(ConfigurationError):
    """Configuration schema validation failed"""
    
    def __init__(self, schema_errors: List[str],
                 config_file: Optional[str] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.schema_errors = schema_errors
        
        if len(schema_errors) == 1:
            message = f"Schema validation failed: {schema_errors[0]}"
        else:
            message = f"Schema validation failed with {len(schema_errors)} errors"
        
        schema_context = context or {}
        schema_context['schema_errors'] = schema_errors
        
        super().__init__(message, config_file, None, schema_context)


class ConfigLoadError(ConfigurationError):
    """Configuration file loading failed"""
    
    def __init__(self, file_path: str, reason: str,
                 original_exception: Optional[Exception] = None,
                 context: Optional[Dict[str, Any]] = None):
        self.file_path = file_path
        self.reason = reason
        
        message = f"Failed to load configuration file '{file_path}': {reason}"
        
        load_context = context or {}
        load_context.update({
            'file_path': file_path,
            'load_reason': reason
        })
        
        super().__init__(message, file_path, None, load_context)
        self.original_exception = original_exception


class ConfigDiscoveryError(ConfigurationError):
    """Configuration discovery failed"""
    
    def __init__(self, search_patterns: List[str], reason: str,
                 context: Optional[Dict[str, Any]] = None):
        self.search_patterns = search_patterns
        self.reason = reason
        
        message = f"Configuration discovery failed: {reason}"
        
        discovery_context = context or {}
        discovery_context.update({
            'search_patterns': search_patterns,
            'discovery_reason': reason
        })
        
        super().__init__(message, None, None, discovery_context)