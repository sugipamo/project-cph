"""
Configuration schema validation
"""
import json
from typing import Dict, Any, List, Optional, Union
from pathlib import Path
from .exceptions import ConfigSchemaError, ConfigValidationError


class ConfigSchemaValidator:
    """JSON Schema-based configuration validation"""
    
    def __init__(self):
        self.schemas = self._load_schemas()
    
    def _load_schemas(self) -> Dict[str, Dict[str, Any]]:
        """Load predefined schemas"""
        return {
            'language_config': {
                'type': 'object',
                'required': ['language_name', 'commands'],
                'properties': {
                    'language_name': {'type': 'string'},
                    'contest_template_path': {'type': 'string'},
                    'contest_stock_path': {'type': 'string'},
                    'contest_temp_path': {'type': 'string'},
                    'commands': {
                        'type': 'object',
                        'patternProperties': {
                            '^[a-zA-Z_][a-zA-Z0-9_]*$': {
                                '$ref': '#/definitions/command_config'
                            }
                        }
                    }
                },
                'definitions': {
                    'command_config': {
                        'type': 'object',
                        'required': ['steps'],
                        'properties': {
                            'steps': {
                                'type': 'array',
                                'items': {'$ref': '#/definitions/step_config'}
                            },
                            'run': {
                                'type': 'array',
                                'items': {'$ref': '#/definitions/step_config'}
                            }
                        }
                    },
                    'step_config': {
                        'type': 'object',
                        'required': ['op'],
                        'properties': {
                            'op': {
                                'type': 'string',
                                'enum': ['mkdir', 'touch', 'copy', 'move', 'remove', 'shell', 'docker', 'python']
                            },
                            'target_path': {'type': 'string'},
                            'source_path': {'type': 'string'},
                            'content': {'type': 'string'},
                            'cmd': {'type': 'string'},
                            'cwd': {'type': 'string'},
                            'allow_failure': {'type': 'boolean'}
                        }
                    }
                }
            },
            'system_config': {
                'type': 'object',
                'properties': {
                    'project_root': {'type': 'string'},
                    'current_contest': {'type': 'string'},
                    'default_language': {'type': 'string'},
                    'workspace_path': {'type': 'string'}
                }
            },
            'execution_context': {
                'type': 'object',
                'required': ['language', 'contest', 'source_file_name'],
                'properties': {
                    'language': {'type': 'string'},
                    'contest': {'type': 'string'},
                    'source_file_name': {'type': 'string'},
                    'workspace_path': {'type': 'string'},
                    'contest_template_path': {'type': 'string'},
                    'contest_stock_path': {'type': 'string'},
                    'contest_temp_path': {'type': 'string'}
                }
            }
        }
    
    def validate_config(self, config: Dict[str, Any], schema_name: str,
                       config_file: Optional[str] = None) -> List[str]:
        """Validate configuration against schema"""
        schema = self.schemas.get(schema_name)
        if not schema:
            raise ConfigSchemaError(
                [f"Unknown schema: {schema_name}"],
                config_file
            )
        
        errors = []
        self._validate_recursive(config, schema, [], errors)
        
        if errors:
            raise ConfigSchemaError(errors, config_file)
        
        return []
    
    def _validate_recursive(self, data: Any, schema: Dict[str, Any],
                           path: List[str], errors: List[str]):
        """Recursively validate data against schema"""
        # Type validation
        expected_type = schema.get('type')
        if expected_type:
            if not self._check_type(data, expected_type):
                path_str = ".".join(path) if path else "root"
                errors.append(f"{path_str}: expected {expected_type}, got {type(data).__name__}")
                return
        
        # Object validation
        if expected_type == 'object' and isinstance(data, dict):
            self._validate_object(data, schema, path, errors)
        
        # Array validation
        elif expected_type == 'array' and isinstance(data, list):
            self._validate_array(data, schema, path, errors)
    
    def _validate_object(self, data: Dict[str, Any], schema: Dict[str, Any],
                        path: List[str], errors: List[str]):
        """Validate object type"""
        # Required properties
        required = schema.get('required', [])
        for req_prop in required:
            if req_prop not in data:
                path_str = ".".join(path + [req_prop])
                errors.append(f"{path_str}: required property missing")
        
        # Property validation
        properties = schema.get('properties', {})
        for prop_name, prop_value in data.items():
            if prop_name in properties:
                prop_schema = properties[prop_name]
                self._validate_recursive(prop_value, prop_schema, path + [prop_name], errors)
        
        # Pattern properties (for dynamic keys)
        pattern_props = schema.get('patternProperties', {})
        for pattern, pattern_schema in pattern_props.items():
            import re
            for prop_name, prop_value in data.items():
                if re.match(pattern, prop_name):
                    self._validate_recursive(prop_value, pattern_schema, path + [prop_name], errors)
    
    def _validate_array(self, data: List[Any], schema: Dict[str, Any],
                       path: List[str], errors: List[str]):
        """Validate array type"""
        items_schema = schema.get('items')
        if items_schema:
            for i, item in enumerate(data):
                self._validate_recursive(item, items_schema, path + [str(i)], errors)
    
    def _check_type(self, data: Any, expected_type: str) -> bool:
        """Check if data matches expected type"""
        type_mapping = {
            'string': str,
            'number': (int, float),
            'integer': int,
            'boolean': bool,
            'array': list,
            'object': dict,
            'null': type(None)
        }
        
        expected_python_type = type_mapping.get(expected_type)
        if expected_python_type is None:
            return True  # Unknown type, allow it
        
        return isinstance(data, expected_python_type)
    
    def validate_language_config(self, config: Dict[str, Any],
                                config_file: Optional[str] = None) -> List[str]:
        """Validate language configuration"""
        return self.validate_config(config, 'language_config', config_file)
    
    def validate_system_config(self, config: Dict[str, Any],
                              config_file: Optional[str] = None) -> List[str]:
        """Validate system configuration"""
        return self.validate_config(config, 'system_config', config_file)
    
    def validate_execution_context(self, context: Dict[str, Any],
                                  config_file: Optional[str] = None) -> List[str]:
        """Validate execution context"""
        return self.validate_config(context, 'execution_context', config_file)
    
    def register_schema(self, name: str, schema: Dict[str, Any]):
        """Register a new schema"""
        self.schemas[name] = schema
    
    def get_schema(self, name: str) -> Optional[Dict[str, Any]]:
        """Get schema by name"""
        return self.schemas.get(name)
    
    def list_schemas(self) -> List[str]:
        """List all available schema names"""
        return list(self.schemas.keys())