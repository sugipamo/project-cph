"""
Configuration template processing system
"""
import re
from typing import Dict, Any, List, Optional, Set
from .exceptions import ConfigTemplateError


class TemplateProcessor:
    """Unified template processing for configuration values"""
    
    # Template pattern: {variable_name} or {variable_name:default_value}
    TEMPLATE_PATTERN = re.compile(r'\{([^}:]+)(?::([^}]*))?\}')
    
    def __init__(self):
        self.global_context = {}
        self.strict_mode = False
    
    def set_global_context(self, context: Dict[str, Any]):
        """Set global template context"""
        self.global_context = context.copy()
    
    def update_global_context(self, context: Dict[str, Any]):
        """Update global template context"""
        self.global_context.update(context)
    
    def set_strict_mode(self, strict: bool):
        """Set strict mode (fail on missing variables)"""
        self.strict_mode = strict
    
    def process_template(self, template: str, context: Optional[Dict[str, Any]] = None,
                        config_file: Optional[str] = None) -> str:
        """Process a single template string"""
        if not isinstance(template, str):
            return template
        
        # Combine contexts (local context overrides global)
        full_context = self.global_context.copy()
        if context:
            full_context.update(context)
        
        # Find all template variables
        matches = self.TEMPLATE_PATTERN.findall(template)
        missing_vars = []
        
        result = template
        for var_name, default_value in matches:
            var_name = var_name.strip()
            placeholder = f"{{{var_name}:{default_value}}}" if default_value else f"{{{var_name}}}"
            
            if var_name in full_context:
                # Replace with actual value
                value = str(full_context[var_name])
                result = result.replace(placeholder, value)
            elif default_value:
                # Use default value
                result = result.replace(placeholder, default_value)
            else:
                # Missing variable
                missing_vars.append(var_name)
                if self.strict_mode:
                    # In strict mode, keep placeholder for error reporting
                    continue
                else:
                    # In non-strict mode, remove placeholder
                    result = result.replace(placeholder, "")
        
        # Handle missing variables
        if missing_vars:
            if self.strict_mode:
                raise ConfigTemplateError(
                    template, missing_vars, config_file
                )
            # In non-strict mode, we already handled missing vars above
        
        return result
    
    def process_config_recursive(self, config: Any, context: Optional[Dict[str, Any]] = None,
                                config_file: Optional[str] = None) -> Any:
        """Recursively process templates in configuration structure"""
        if isinstance(config, str):
            return self.process_template(config, context, config_file)
        
        elif isinstance(config, dict):
            result = {}
            for key, value in config.items():
                # Process both key and value
                processed_key = self.process_template(key, context, config_file) if isinstance(key, str) else key
                processed_value = self.process_config_recursive(value, context, config_file)
                result[processed_key] = processed_value
            return result
        
        elif isinstance(config, list):
            return [self.process_config_recursive(item, context, config_file) for item in config]
        
        else:
            # Non-string types are returned as-is
            return config
    
    def extract_template_variables(self, template: str) -> Set[str]:
        """Extract all template variables from a template string"""
        if not isinstance(template, str):
            return set()
        
        matches = self.TEMPLATE_PATTERN.findall(template)
        return {var_name.strip() for var_name, _ in matches}
    
    def extract_config_variables(self, config: Any) -> Set[str]:
        """Extract all template variables from configuration structure"""
        variables = set()
        
        if isinstance(config, str):
            variables.update(self.extract_template_variables(config))
        
        elif isinstance(config, dict):
            for key, value in config.items():
                if isinstance(key, str):
                    variables.update(self.extract_template_variables(key))
                variables.update(self.extract_config_variables(value))
        
        elif isinstance(config, list):
            for item in config:
                variables.update(self.extract_config_variables(item))
        
        return variables
    
    def validate_template_context(self, template: str, context: Dict[str, Any],
                                 config_file: Optional[str] = None) -> List[str]:
        """Validate that context provides all required template variables"""
        required_vars = self.extract_template_variables(template)
        missing_vars = []
        
        for var in required_vars:
            if var not in context:
                # Check if variable has default value
                matches = self.TEMPLATE_PATTERN.findall(template)
                has_default = any(var_name.strip() == var and default for var_name, default in matches)
                
                if not has_default:
                    missing_vars.append(var)
        
        return missing_vars
    
    def validate_config_context(self, config: Any, context: Dict[str, Any],
                               config_file: Optional[str] = None) -> List[str]:
        """Validate that context provides all required variables in config"""
        required_vars = self.extract_config_variables(config)
        missing_vars = []
        
        full_context = self.global_context.copy()
        full_context.update(context)
        
        for var in required_vars:
            if var not in full_context:
                missing_vars.append(var)
        
        return missing_vars
    
    def create_template_context(self, language: str, contest: str, source_file_name: str,
                               **additional_vars) -> Dict[str, Any]:
        """Create standard template context for CPH configurations"""
        context = {
            'language': language,
            'language_name': language,
            'contest': contest,
            'source_file_name': source_file_name,
            'source_base_name': source_file_name.rsplit('.', 1)[0] if '.' in source_file_name else source_file_name
        }
        
        # Add additional variables
        context.update(additional_vars)
        
        return context
    
    def preview_template(self, template: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Preview template processing without actually processing"""
        variables = self.extract_template_variables(template)
        
        preview = {
            'template': template,
            'variables_found': list(variables),
            'context_provided': list(context.keys()),
            'missing_variables': [var for var in variables if var not in context],
            'preview_result': None
        }
        
        try:
            preview['preview_result'] = self.process_template(template, context)
        except ConfigTemplateError as e:
            preview['error'] = str(e)
        
        return preview


# Global template processor instance
default_processor = TemplateProcessor()


def process_template(template: str, context: Optional[Dict[str, Any]] = None,
                    config_file: Optional[str] = None) -> str:
    """Global template processing function"""
    return default_processor.process_template(template, context, config_file)


def process_config(config: Any, context: Optional[Dict[str, Any]] = None,
                  config_file: Optional[str] = None) -> Any:
    """Global config processing function"""
    return default_processor.process_config_recursive(config, context, config_file)