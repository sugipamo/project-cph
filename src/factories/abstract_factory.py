"""
Abstract factory interface
"""
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional


class AbstractRequestFactory(ABC):
    """Abstract factory for request creation"""
    
    @abstractmethod
    def create_request(self, request_type: str, **kwargs) -> Any:
        """
        Create a request of the specified type
        
        Args:
            request_type: Type of request to create
            **kwargs: Parameters for request creation
            
        Returns:
            Created request instance
        """
        pass
    
    @abstractmethod
    def supports_type(self, request_type: str) -> bool:
        """
        Check if factory supports the given request type
        
        Args:
            request_type: Type to check
            
        Returns:
            True if supported, False otherwise
        """
        pass
    
    @abstractmethod
    def get_supported_types(self) -> list:
        """
        Get list of supported request types
        
        Returns:
            List of supported type strings
        """
        pass


class AbstractDriverFactory(ABC):
    """Abstract factory for driver creation"""
    
    @abstractmethod
    def create_driver(self, driver_type: str, **kwargs) -> Any:
        """
        Create a driver of the specified type
        
        Args:
            driver_type: Type of driver to create
            **kwargs: Parameters for driver creation
            
        Returns:
            Created driver instance
        """
        pass
    
    @abstractmethod
    def auto_configure(self, environment: str) -> Dict[str, Any]:
        """
        Auto-configure drivers for specific environment
        
        Args:
            environment: Environment name (e.g., 'test', 'ci', 'production')
            
        Returns:
            Dictionary of configured drivers
        """
        pass