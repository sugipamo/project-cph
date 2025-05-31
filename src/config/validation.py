"""
Unified configuration validation system
"""
from typing import Dict, Any, List, Optional, Union, Tuple
from pathlib import Path
from .schema import ConfigSchemaValidator
from .template import TemplateProcessor
from .exceptions import ConfigValidationError, ConfigTemplateError


class ConfigValidationResult:
    """Result of configuration validation"""
    
    def __init__(self):
        self.is_valid = True
        self.errors: List[str] = []
        self.warnings: List[str] = []
        self.info: List[str] = []
        self.validated_config: Optional[Dict[str, Any]] = None
    
    def add_error(self, message: str):
        """Add validation error"""
        self.errors.append(message)
        self.is_valid = False
    
    def add_warning(self, message: str):
        """Add validation warning"""
        self.warnings.append(message)
    
    def add_info(self, message: str):
        """Add validation info"""
        self.info.append(message)
    
    def has_errors(self) -> bool:
        """Check if validation has errors"""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if validation has warnings"""
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """Get validation summary"""
        status = "VALID" if self.is_valid else "INVALID"
        return f"Validation {status}: {len(self.errors)} errors, {len(self.warnings)} warnings"
    
    def get_detailed_report(self) -> str:
        """Get detailed validation report"""
        lines = [self.get_summary(), ""]
        
        if self.errors:
            lines.append("ERRORS:")
            for error in self.errors:
                lines.append(f"  - {error}")
            lines.append("")
        
        if self.warnings:
            lines.append("WARNINGS:")
            for warning in self.warnings:
                lines.append(f"  - {warning}")
            lines.append("")
        
        if self.info:
            lines.append("INFO:")
            for info in self.info:
                lines.append(f"  - {info}")
        
        return "\n".join(lines)


class UnifiedConfigValidator:
    """Single source of truth for all configuration validation"""
    
    def __init__(self):
        self.schema_validator = ConfigSchemaValidator()
        self.template_processor = TemplateProcessor()
        self.custom_validators = {}
    
    def register_custom_validator(self, config_type: str, validator_func):
        """Register custom validation function for specific config type"""
        self.custom_validators[config_type] = validator_func
    
    def validate_complete_config(self, config: Dict[str, Any], config_type: str,
                                config_file: Optional[str] = None,
                                context: Optional[Dict[str, Any]] = None) -> ConfigValidationResult:
        """Validate entire configuration tree"""
        result = ConfigValidationResult()
        
        try:
            # 1. Schema validation
            self._validate_schema(config, config_type, config_file, result)
            
            # 2. Template validation
            if context:
                self._validate_templates(config, context, config_file, result)
            
            # 3. Semantic validation
            self._validate_semantics(config, config_type, config_file, result)
            
            # 4. Custom validation
            if config_type in self.custom_validators:
                self._run_custom_validation(config, config_type, config_file, result)
            
            # 5. Cross-reference validation
            self._validate_cross_references(config, config_type, config_file, result)
            
            if result.is_valid:
                result.validated_config = config.copy()
        
        except Exception as e:
            result.add_error(f"Validation failed with exception: {str(e)}")
        
        return result
    
    def _validate_schema(self, config: Dict[str, Any], config_type: str,
                        config_file: Optional[str], result: ConfigValidationResult):
        """Validate configuration against schema"""
        try:
            self.schema_validator.validate_config(config, config_type, config_file)
            result.add_info(f"Schema validation passed for {config_type}")
        except Exception as e:
            result.add_error(f"Schema validation failed: {str(e)}")
    
    def _validate_templates(self, config: Dict[str, Any], context: Dict[str, Any],
                           config_file: Optional[str], result: ConfigValidationResult):
        """Validate template variables and processing"""
        try:
            # Extract all template variables from config
            required_vars = self.template_processor.extract_config_variables(config)
            missing_vars = self.template_processor.validate_config_context(config, context, config_file)
            
            if missing_vars:
                result.add_error(f"Missing template variables: {', '.join(missing_vars)}")
            else:
                result.add_info(f"Template validation passed: {len(required_vars)} variables resolved")
            
            # Try to process templates to check for errors
            try:
                processed_config = self.template_processor.process_config_recursive(config, context, config_file)
                result.add_info("Template processing test passed")
            except ConfigTemplateError as e:
                result.add_error(f"Template processing failed: {str(e)}")
        
        except Exception as e:
            result.add_error(f"Template validation failed: {str(e)}")
    
    def _validate_semantics(self, config: Dict[str, Any], config_type: str,
                           config_file: Optional[str], result: ConfigValidationResult):
        """Validate semantic correctness of configuration"""
        if config_type == 'language_config':
            self._validate_language_config_semantics(config, config_file, result)
        elif config_type == 'system_config':
            self._validate_system_config_semantics(config, config_file, result)
        elif config_type == 'execution_context':
            self._validate_execution_context_semantics(config, config_file, result)
    
    def _validate_language_config_semantics(self, config: Dict[str, Any],
                                           config_file: Optional[str], result: ConfigValidationResult):
        """Validate language configuration semantics"""
        # Check if language_name matches expected patterns
        language_name = config.get('language_name', '')
        if not language_name.isalnum():
            result.add_warning(f"Language name '{language_name}' contains non-alphanumeric characters")
        
        # Validate commands structure
        commands = config.get('commands', {})
        for command_name, command_config in commands.items():
            if not isinstance(command_config, dict):
                result.add_error(f"Command '{command_name}' configuration must be an object")
                continue
            
            # Check for either 'steps' or 'run' arrays
            has_steps = 'steps' in command_config
            has_run = 'run' in command_config
            
            if not has_steps and not has_run:
                result.add_error(f"Command '{command_name}' must have either 'steps' or 'run' array")
            elif has_steps and has_run:
                result.add_warning(f"Command '{command_name}' has both 'steps' and 'run' arrays - 'steps' will be used")
            
            # Validate steps/run content
            steps = command_config.get('steps', command_config.get('run', []))
            if not isinstance(steps, list):
                result.add_error(f"Command '{command_name}' steps must be an array")
                continue
            
            for i, step in enumerate(steps):
                self._validate_step_semantics(step, f"{command_name}[{i}]", result)
    
    def _validate_step_semantics(self, step: Dict[str, Any], step_path: str,
                                result: ConfigValidationResult):
        """Validate individual step semantics"""
        if not isinstance(step, dict):
            result.add_error(f"Step {step_path} must be an object")
            return
        
        op = step.get('op')
        if not op:
            result.add_error(f"Step {step_path} missing required 'op' field")
            return
        
        # Validate operation-specific requirements
        if op in ['mkdir', 'touch', 'copy', 'move', 'remove']:
            if 'target_path' not in step:
                result.add_error(f"Step {step_path} with op '{op}' requires 'target_path'")
        
        elif op in ['copy', 'move']:
            if 'source_path' not in step:
                result.add_error(f"Step {step_path} with op '{op}' requires 'source_path'")
        
        elif op == 'shell':
            if 'cmd' not in step:
                result.add_error(f"Step {step_path} with op 'shell' requires 'cmd'")
        
        elif op == 'docker':
            if 'cmd' not in step:
                result.add_error(f"Step {step_path} with op 'docker' requires 'cmd'")
        
        elif op == 'python':
            if 'cmd' not in step and 'content' not in step:
                result.add_error(f"Step {step_path} with op 'python' requires either 'cmd' or 'content'")
        
        # Check for common mistakes
        if 'allow_failure' in step:
            allow_failure = step['allow_failure']
            if not isinstance(allow_failure, bool):
                result.add_warning(f"Step {step_path} 'allow_failure' should be boolean, got {type(allow_failure).__name__}")
    
    def _validate_system_config_semantics(self, config: Dict[str, Any],
                                         config_file: Optional[str], result: ConfigValidationResult):
        """Validate system configuration semantics"""
        # Validate paths exist if they're absolute
        for path_key in ['project_root', 'workspace_path']:
            if path_key in config:
                path_value = config[path_key]
                if isinstance(path_value, str) and path_value.startswith('/'):
                    path_obj = Path(path_value)
                    if not path_obj.exists():
                        result.add_warning(f"Path '{path_key}' does not exist: {path_value}")
    
    def _validate_execution_context_semantics(self, config: Dict[str, Any],
                                             config_file: Optional[str], result: ConfigValidationResult):
        """Validate execution context semantics"""
        # Validate source file name
        source_file = config.get('source_file_name', '')
        if source_file and not source_file.strip():
            result.add_error("source_file_name cannot be empty or whitespace")
        
        # Validate language
        language = config.get('language', '')
        if not language.isalnum():
            result.add_warning(f"Language '{language}' contains non-alphanumeric characters")
    
    def _run_custom_validation(self, config: Dict[str, Any], config_type: str,
                              config_file: Optional[str], result: ConfigValidationResult):
        """Run custom validation function"""
        try:
            validator_func = self.custom_validators[config_type]
            custom_result = validator_func(config, config_file)
            
            # Merge custom validation results
            if hasattr(custom_result, 'errors'):
                result.errors.extend(custom_result.errors)
            if hasattr(custom_result, 'warnings'):
                result.warnings.extend(custom_result.warnings)
            if hasattr(custom_result, 'is_valid') and not custom_result.is_valid:
                result.is_valid = False
        
        except Exception as e:
            result.add_error(f"Custom validation failed: {str(e)}")
    
    def _validate_cross_references(self, config: Dict[str, Any], config_type: str,
                                  config_file: Optional[str], result: ConfigValidationResult):
        """Validate cross-references within configuration"""
        if config_type == 'language_config':
            # Check for circular dependencies in commands
            commands = config.get('commands', {})
            self._check_command_dependencies(commands, result)
    
    def _check_command_dependencies(self, commands: Dict[str, Any], result: ConfigValidationResult):
        """Check for circular dependencies in command definitions"""
        # This is a simplified check - could be more sophisticated
        for command_name in commands:
            if self._has_circular_dependency(command_name, commands, set()):
                result.add_warning(f"Potential circular dependency detected in command '{command_name}'")
    
    def _has_circular_dependency(self, command: str, commands: Dict[str, Any],
                                visited: set) -> bool:
        """Check for circular dependency (simplified implementation)"""
        if command in visited:
            return True
        
        visited.add(command)
        
        # Check if this command references other commands
        command_config = commands.get(command, {})
        steps = command_config.get('steps', command_config.get('run', []))
        
        for step in steps:
            if isinstance(step, dict) and step.get('op') == 'shell':
                cmd = step.get('cmd', '')
                # Simple check for command references (could be more sophisticated)
                for other_command in commands:
                    if other_command != command and other_command in cmd:
                        if self._has_circular_dependency(other_command, commands, visited.copy()):
                            return True
        
        return False
    
    def validate_runtime_context(self, context: Dict[str, Any],
                                config_file: Optional[str] = None) -> ConfigValidationResult:
        """Validate runtime execution context"""
        result = ConfigValidationResult()
        
        try:
            # Validate required context fields
            required_fields = ['language', 'contest', 'source_file_name']
            for field in required_fields:
                if field not in context:
                    result.add_error(f"Missing required context field: {field}")
                elif not context[field]:
                    result.add_error(f"Context field '{field}' cannot be empty")
            
            # Validate field formats
            if 'language' in context:
                language = context['language']
                if not isinstance(language, str) or not language.isalnum():
                    result.add_error(f"Language must be alphanumeric string, got: {language}")
            
            if 'source_file_name' in context:
                source_file = context['source_file_name']
                if not isinstance(source_file, str):
                    result.add_error(f"source_file_name must be string, got: {type(source_file).__name__}")
                elif '/' in source_file or '\\' in source_file:
                    result.add_warning("source_file_name should not contain path separators")
            
            # Validate paths if present
            path_fields = ['workspace_path', 'contest_template_path', 'contest_stock_path', 'contest_temp_path']
            for field in path_fields:
                if field in context:
                    path_value = context[field]
                    if isinstance(path_value, str) and path_value:
                        # Template validation will be done separately
                        if not ('{' in path_value and '}' in path_value):
                            # Not a template, validate as actual path
                            path_obj = Path(path_value)
                            if path_obj.is_absolute() and not path_obj.exists():
                                result.add_warning(f"Path '{field}' does not exist: {path_value}")
            
            if result.is_valid:
                result.validated_config = context.copy()
                result.add_info("Runtime context validation passed")
        
        except Exception as e:
            result.add_error(f"Runtime context validation failed: {str(e)}")
        
        return result
    
    def validate_config_file(self, file_path: Union[str, Path], config_type: str,
                            context: Optional[Dict[str, Any]] = None) -> ConfigValidationResult:
        """Validate configuration file"""
        from .discovery import ConfigDiscovery
        
        result = ConfigValidationResult()
        
        try:
            discovery = ConfigDiscovery()
            config = discovery.load_config(file_path)
            
            return self.validate_complete_config(config, config_type, str(file_path), context)
        
        except Exception as e:
            result.add_error(f"Failed to load and validate config file: {str(e)}")
            return result