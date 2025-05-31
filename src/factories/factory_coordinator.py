"""
Factory coordinator for managing multiple factories
"""
from typing import Dict, List, Any, Optional
from .abstract_factory import AbstractRequestFactory, AbstractDriverFactory


class FactoryCoordinator:
    """
    Coordinates multiple factories and provides unified interface
    """
    
    def __init__(self):
        self._request_factories: Dict[str, AbstractRequestFactory] = {}
        self._driver_factories: Dict[str, AbstractDriverFactory] = {}
        self._default_request_factory: Optional[AbstractRequestFactory] = None
        self._default_driver_factory: Optional[AbstractDriverFactory] = None
    
    def register_request_factory(self, name: str, factory: AbstractRequestFactory, 
                                is_default: bool = False):
        """
        Register a request factory
        
        Args:
            name: Factory name
            factory: Factory instance
            is_default: Whether this is the default factory
        """
        self._request_factories[name] = factory
        if is_default or self._default_request_factory is None:
            self._default_request_factory = factory
    
    def register_driver_factory(self, name: str, factory: AbstractDriverFactory,
                               is_default: bool = False):
        """
        Register a driver factory
        
        Args:
            name: Factory name
            factory: Factory instance
            is_default: Whether this is the default factory
        """
        self._driver_factories[name] = factory
        if is_default or self._default_driver_factory is None:
            self._default_driver_factory = factory
    
    def create_request(self, request_type: str, factory_name: str = None, **kwargs) -> Any:
        """
        Create a request using specified or default factory
        
        Args:
            request_type: Type of request to create
            factory_name: Specific factory to use (optional)
            **kwargs: Parameters for request creation
            
        Returns:
            Created request instance
        """
        factory = self._get_request_factory(factory_name, request_type)
        if not factory:
            raise ValueError(f"No factory found that supports request type: {request_type}")
        
        return factory.create_request(request_type, **kwargs)
    
    def create_driver(self, driver_type: str, factory_name: str = None, **kwargs) -> Any:
        """
        Create a driver using specified or default factory
        
        Args:
            driver_type: Type of driver to create
            factory_name: Specific factory to use (optional)
            **kwargs: Parameters for driver creation
            
        Returns:
            Created driver instance
        """
        factory = self._get_driver_factory(factory_name)
        if not factory:
            raise ValueError("No driver factory available")
        
        return factory.create_driver(driver_type, **kwargs)
    
    def auto_configure_for_environment(self, environment: str) -> Dict[str, Any]:
        """
        Auto-configure all factories for specific environment
        
        Args:
            environment: Environment name
            
        Returns:
            Dictionary of configured components
        """
        result = {}
        
        # Configure drivers
        if self._default_driver_factory:
            result['drivers'] = self._default_driver_factory.auto_configure(environment)
        
        return result
    
    def get_supported_request_types(self) -> List[str]:
        """Get all supported request types across all factories"""
        types = set()
        for factory in self._request_factories.values():
            types.update(factory.get_supported_types())
        return list(types)
    
    def _get_request_factory(self, factory_name: str, request_type: str) -> Optional[AbstractRequestFactory]:
        """Get appropriate request factory"""
        if factory_name:
            factory = self._request_factories.get(factory_name)
            if factory and factory.supports_type(request_type):
                return factory
        
        # Try to find a factory that supports the request type
        for factory in self._request_factories.values():
            if factory.supports_type(request_type):
                return factory
        
        return None
    
    def _get_driver_factory(self, factory_name: str) -> Optional[AbstractDriverFactory]:
        """Get appropriate driver factory"""
        if factory_name:
            return self._driver_factories.get(factory_name)
        
        return self._default_driver_factory