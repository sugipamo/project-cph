"""
Basic validation service for environment JSON files
"""
from typing import Dict, Any, Optional


class ValidationService:
    """Simple validation service for env.json files"""
    
    @staticmethod
    def validate_env_json(data: Dict[str, Any], path: str, shared_config: Optional[Dict[str, Any]] = None) -> bool:
        """
        Basic validation for env.json files
        
        Args:
            data: The env.json data to validate
            path: Path to the env.json file (for error reporting)
            shared_config: Optional shared configuration
            
        Returns:
            bool: True if valid, raises exception if invalid
            
        Raises:
            ValueError: If validation fails
        """
        if not isinstance(data, dict):
            raise ValueError(f"Invalid env.json format in {path}: root must be a dictionary")
        
        # Check that at least one language is defined
        language_keys = [key for key in data.keys() if key not in ['shared', '__common__', 'common', 'base']]
        if not language_keys:
            raise ValueError(f"No language configurations found in {path}")
        
        # Basic structure validation for each language
        for lang_key, lang_config in data.items():
            if lang_key in ['shared', '__common__', 'common', 'base']:
                continue
                
            if not isinstance(lang_config, dict):
                raise ValueError(f"Language configuration for '{lang_key}' in {path} must be a dictionary")
        
        return True