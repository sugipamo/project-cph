"""
Request builders for the unified factory pattern

This module provides backward compatibility for the request builders.
"""
from typing import Dict, Any, List, Optional


class RequestBuilder:
    """Base class for request builders"""
    
    def build_from_step(self, run_step, factory):
        """Build request from run step"""
        raise NotImplementedError
    
    def build_from_node(self, node, factory):
        """Build request from ConfigNode"""
        raise NotImplementedError
    
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build request from kwargs"""
        raise NotImplementedError


class RequestBuilders:
    """Legacy request builders collection"""
    
    def __init__(self):
        self._builders = {}
    
    def has_builder(self, command_type) -> bool:
        """Check if builder exists for command type"""
        return command_type in self._builders
    
    def get_registered_types(self) -> List:
        """Get list of registered command types"""
        return list(self._builders.keys())
    
    def register_builder(self, command_type, builder):
        """Register a builder for a command type"""
        self._builders[command_type] = builder
    
    def get_builder(self, command_type):
        """Get builder for command type"""
        return self._builders.get(command_type)


# Backward compatibility exports
__all__ = ['RequestBuilder', 'RequestBuilders']