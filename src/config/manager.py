"""
Unified configuration management system
"""
import os
from pathlib import Path
from typing import Dict, Any, List, Optional, Union
from .discovery import ConfigDiscovery
from .validation import UnifiedConfigValidator, ConfigValidationResult
from .schema import ConfigSchemaValidator
from .template import TemplateProcessor
from .cache import ConfigCache
from .exceptions import ConfigurationError, ConfigLoadError, ConfigValidationError
from ..core.exceptions import ErrorLogger


class UnifiedConfig:
    """Unified configuration container"""
    
    def __init__(self):
        self.language_configs: Dict[str, Dict[str, Any]] = {}
        self.system_config: Dict[str, Any] = {}
        self.execution_context: Dict[str, Any] = {}
        self.raw_configs: Dict[str, Dict[str, Any]] = {}
        self.validation_results: Dict[str, ConfigValidationResult] = {}
        self._template_processor = TemplateProcessor()
    
    def get_language_config(self, language: str) -> Optional[Dict[str, Any]]:
        """Get configuration for specific language"""
        return self.language_configs.get(language)
    
    def get_system_config(self) -> Dict[str, Any]:
        """Get system configuration"""
        return self.system_config
    
    def get_execution_context(self) -> Dict[str, Any]:
        """Get execution context"""
        return self.execution_context
    
    def set_execution_context(self, context: Dict[str, Any]):
        """Set execution context and update template processor"""
        self.execution_context = context.copy()
        self._template_processor.set_global_context(context)
    
    def resolve_path(self, path: List[str], language: Optional[str] = None,
                    default: Any = None) -> Any:
        """Resolve configuration path with fallback logic"""
        # Try language-specific config first
        if language and language in self.language_configs:
            result = self._resolve_path_in_config(path, self.language_configs[language])
            if result is not None:
                return self._process_template_if_string(result)
        
        # Try system config
        result = self._resolve_path_in_config(path, self.system_config)
        if result is not None:
            return self._process_template_if_string(result)
        
        # Return default
        return default
    
    def _resolve_path_in_config(self, path: List[str], config: Dict[str, Any]) -> Any:
        """Resolve path in specific configuration"""
        current = config
        for key in path:
            if isinstance(current, dict) and key in current:
                current = current[key]
            else:
                return None
        return current
    
    def _process_template_if_string(self, value: Any) -> Any:
        """Process template if value is a string"""
        if isinstance(value, str):
            return self._template_processor.process_template(value, self.execution_context)
        return value
    
    def get_command_config(self, language: str, command: str) -> Optional[Dict[str, Any]]:
        """Get command configuration for language"""
        lang_config = self.get_language_config(language)
        if not lang_config:
            return None
        
        commands = lang_config.get('commands', {})
        return commands.get(command)
    
    def get_command_steps(self, language: str, command: str) -> List[Dict[str, Any]]:
        """Get command steps with template processing"""
        command_config = self.get_command_config(language, command)
        if not command_config:
            return []
        
        # Support both 'steps' and 'run' arrays
        steps = command_config.get('steps', command_config.get('run', []))
        
        # Process templates in steps
        processed_steps = self._template_processor.process_config_recursive(
            steps, self.execution_context
        )
        
        return processed_steps if isinstance(processed_steps, list) else []
    
    def list_languages(self) -> List[str]:
        """List all available languages"""
        return list(self.language_configs.keys())
    
    def list_commands(self, language: str) -> List[str]:
        """List all commands for a language"""
        lang_config = self.get_language_config(language)
        if not lang_config:
            return []
        
        commands = lang_config.get('commands', {})
        return list(commands.keys())
    
    def is_valid(self) -> bool:
        """Check if all configurations are valid"""
        return all(result.is_valid for result in self.validation_results.values())
    
    def get_validation_summary(self) -> str:
        """Get validation summary for all configurations"""
        if not self.validation_results:
            return "No validation results available"
        
        total_errors = sum(len(result.errors) for result in self.validation_results.values())
        total_warnings = sum(len(result.warnings) for result in self.validation_results.values())
        
        status = "VALID" if self.is_valid() else "INVALID"
        return f"Configuration {status}: {total_errors} errors, {total_warnings} warnings"
    
    def get_detailed_validation_report(self) -> str:
        """Get detailed validation report"""
        lines = [self.get_validation_summary(), ""]
        
        for config_name, result in self.validation_results.items():
            lines.append(f"=== {config_name} ===")
            lines.append(result.get_detailed_report())
            lines.append("")
        
        return "\n".join(lines)


class ConfigurationManager:
    """Unified configuration management system"""
    
    def __init__(self, project_root: Optional[Union[str, Path]] = None,
                 enable_cache: bool = True, enable_validation: bool = True):
        self.project_root = Path(project_root) if project_root else Path.cwd()
        self.enable_cache = enable_cache
        self.enable_validation = enable_validation
        
        # Core components
        self.discovery = ConfigDiscovery(self.project_root)
        self.validator = UnifiedConfigValidator()
        self.schema_validator = ConfigSchemaValidator()
        self.template_processor = TemplateProcessor()
        self.cache = ConfigCache(enable_cache)
        self.logger = ErrorLogger()
        
        # State
        self._current_config: Optional[UnifiedConfig] = None
        self._environment = "default"
    
    def load_config(self, environment: str = "default",
                   context: Optional[Dict[str, Any]] = None) -> UnifiedConfig:
        """Load and validate complete configuration"""
        self._environment = environment
        
        # Check cache first
        if self.enable_cache:
            cache_key = f"unified_config_{environment}"
            cached_config = self._get_cached_unified_config(cache_key, context)
            if cached_config:
                self.logger.log_execution_success("config_load", 0, "Configuration loaded from cache")
                self._current_config = cached_config
                return cached_config
        
        self.logger.log_execution_start("config_load", {"environment": environment})
        start_time = __import__('time').time()
        
        try:
            # Discover and load all configurations
            unified_config = UnifiedConfig()
            
            # Load language configurations
            self._load_language_configs(unified_config)
            
            # Load system configuration
            self._load_system_config(unified_config)
            
            # Set execution context
            if context:
                unified_config.set_execution_context(context)
            
            # Validate configurations
            if self.enable_validation:
                self._validate_all_configs(unified_config)
            
            # Cache the result
            if self.enable_cache:
                self._cache_unified_config(cache_key, unified_config, context)
            
            duration = __import__('time').time() - start_time
            self.logger.log_execution_success(
                "config_load", duration,
                f"Loaded {len(unified_config.language_configs)} language configs"
            )
            
            self._current_config = unified_config
            return unified_config
        
        except Exception as e:
            self.logger.log_operation_error("config_load", e)
            raise ConfigurationError(f"Failed to load configuration: {str(e)}") from e
    
    def _load_language_configs(self, unified_config: UnifiedConfig):
        """Load all language configurations"""
        discovered_configs = self.discovery.discover_configs()
        
        for config_key, file_path in discovered_configs.items():
            if config_key.startswith("language_"):
                try:
                    language = config_key.replace("language_", "")
                    config = self.discovery.load_config(file_path)
                    
                    unified_config.language_configs[language] = config
                    unified_config.raw_configs[config_key] = config
                    
                except ConfigLoadError as e:
                    self.logger.log_operation_error("language_config_load", e)
                    # Continue loading other configs
                    continue
    
    def _load_system_config(self, unified_config: UnifiedConfig):
        """Load system configuration"""
        # Try to find system config file
        system_config_path = self.project_root / "system_info.json"
        
        if system_config_path.exists():
            try:
                config = self.discovery.load_config(system_config_path)
                unified_config.system_config = config
                unified_config.raw_configs["system"] = config
            
            except ConfigLoadError as e:
                self.logger.log_operation_error("system_config_load", e)
        
        # Add project root to system config
        unified_config.system_config["project_root"] = str(self.project_root)
    
    def _validate_all_configs(self, unified_config: UnifiedConfig):
        """Validate all loaded configurations"""
        # Validate language configurations
        for language, config in unified_config.language_configs.items():
            try:
                result = self.validator.validate_complete_config(
                    config, "language_config", 
                    config_file=f"contest_env/{language}/env.json",
                    context=unified_config.execution_context
                )
                unified_config.validation_results[f"language_{language}"] = result
                
                if not result.is_valid:
                    self.logger.log_validation_error(
                        f"language_config_{language}",
                        config,
                        f"Validation failed: {len(result.errors)} errors"
                    )
            
            except Exception as e:
                self.logger.log_operation_error(f"validate_language_{language}", e)
        
        # Validate system configuration
        if unified_config.system_config:
            try:
                result = self.validator.validate_complete_config(
                    unified_config.system_config, "system_config",
                    config_file="system_info.json"
                )
                unified_config.validation_results["system"] = result
            
            except Exception as e:
                self.logger.log_operation_error("validate_system_config", e)
        
        # Validate execution context
        if unified_config.execution_context:
            try:
                result = self.validator.validate_runtime_context(
                    unified_config.execution_context
                )
                unified_config.validation_results["execution_context"] = result
            
            except Exception as e:
                self.logger.log_operation_error("validate_execution_context", e)
    
    def _get_cached_unified_config(self, cache_key: str, 
                                  context: Optional[Dict[str, Any]]) -> Optional[UnifiedConfig]:
        """Get cached unified configuration"""
        # This is a simplified cache implementation
        # In practice, you'd need to serialize/deserialize UnifiedConfig
        return None  # Disable for now due to complexity
    
    def _cache_unified_config(self, cache_key: str, config: UnifiedConfig,
                             context: Optional[Dict[str, Any]]):
        """Cache unified configuration"""
        # This is a simplified cache implementation
        # In practice, you'd need to serialize/deserialize UnifiedConfig
        pass  # Disable for now due to complexity
    
    def get_current_config(self) -> Optional[UnifiedConfig]:
        """Get currently loaded configuration"""
        return self._current_config
    
    def reload_config(self, context: Optional[Dict[str, Any]] = None) -> UnifiedConfig:
        """Reload configuration from files"""
        self.cache.clear_cache()
        return self.load_config(self._environment, context)
    
    def get_language_config(self, language: str,
                           context: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Get configuration for specific language"""
        if not self._current_config:
            self.load_config(context=context)
        
        config = self._current_config.get_language_config(language)
        if not config:
            raise ConfigurationError(f"Language configuration not found: {language}")
        
        # Process templates with current context
        if context:
            config = self.template_processor.process_config_recursive(config, context)
        
        return config
    
    def resolve_config_path(self, path: List[str], language: Optional[str] = None,
                           context: Optional[Dict[str, Any]] = None,
                           default: Any = None) -> Any:
        """Resolve configuration path with context"""
        if not self._current_config:
            self.load_config(context=context)
        
        # Update context if provided
        if context:
            self._current_config.set_execution_context(context)
        
        return self._current_config.resolve_path(path, language, default)
    
    def get_command_steps(self, language: str, command: str,
                         context: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Get command steps with template processing"""
        if not self._current_config:
            self.load_config(context=context)
        
        # Update context if provided
        if context:
            self._current_config.set_execution_context(context)
        
        return self._current_config.get_command_steps(language, command)
    
    def validate_configuration(self, force_reload: bool = False) -> ConfigValidationResult:
        """Validate current configuration"""
        if force_reload or not self._current_config:
            self.reload_config()
        
        # Create combined validation result
        result = ConfigValidationResult()
        
        if self._current_config:
            for config_name, validation_result in self._current_config.validation_results.items():
                result.errors.extend([f"{config_name}: {error}" for error in validation_result.errors])
                result.warnings.extend([f"{config_name}: {warning}" for warning in validation_result.warnings])
                if not validation_result.is_valid:
                    result.is_valid = False
        
        return result
    
    def list_available_languages(self) -> List[str]:
        """List all available languages"""
        if not self._current_config:
            self.load_config()
        
        return self._current_config.list_languages()
    
    def list_language_commands(self, language: str) -> List[str]:
        """List all commands for a language"""
        if not self._current_config:
            self.load_config()
        
        return self._current_config.list_commands(language)
    
    def get_config_info(self) -> Dict[str, Any]:
        """Get comprehensive configuration information"""
        return {
            'project_root': str(self.project_root),
            'environment': self._environment,
            'cache_enabled': self.enable_cache,
            'validation_enabled': self.enable_validation,
            'discovered_files': self.discovery.get_config_info(),
            'cache_stats': self.cache.get_cache_stats(),
            'current_config_valid': self._current_config.is_valid() if self._current_config else None,
            'available_languages': self.list_available_languages() if self._current_config else []
        }


# Global configuration manager instance
default_manager = ConfigurationManager()