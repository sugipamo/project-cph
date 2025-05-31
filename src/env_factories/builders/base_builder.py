"""
Base request builder
"""
from abc import ABC, abstractmethod
from typing import Dict, Any


class RequestBuilder(ABC):
    """Base class for request builders"""
    
    @abstractmethod
    def build_from_step(self, run_step, factory):
        """Build request from run step"""
        pass
    
    @abstractmethod
    def build_from_node(self, node, factory):
        """Build request from ConfigNode"""
        pass
    
    @abstractmethod
    def build_from_kwargs(self, kwargs: Dict[str, Any], factory):
        """Build request from keyword arguments"""
        pass
    
    def _format_cmd_array(self, cmd, **format_kwargs):
        """Format command array with given parameters"""
        if isinstance(cmd, list):
            return [self._format_string(item, **format_kwargs) if isinstance(item, str) else item for item in cmd]
        return cmd
    
    def _format_string(self, template: str, **format_kwargs) -> str:
        """Format string template with given parameters"""
        if not isinstance(template, str):
            return template
        
        result = template
        for key, value in format_kwargs.items():
            placeholder = f"{{{key}}}"
            if placeholder in result:
                result = result.replace(placeholder, str(value))
        
        return result