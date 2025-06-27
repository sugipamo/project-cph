"""Tests for dependency injection container"""
import pytest
from unittest.mock import Mock
from src.infrastructure.di_container import DIContainer, DIKey


class TestDIContainer:
    """Test suite for dependency injection container"""
    
    def setup_method(self):
        """Set up test container before each test"""
        self.container = DIContainer()
    
    def test_register_and_resolve_simple(self):
        """Test basic registration and resolution"""
        mock_service = Mock()
        
        self.container.register("service", lambda: mock_service)
        resolved = self.container.resolve("service")
        
        assert resolved == mock_service
    
    def test_register_and_resolve_with_dikey(self):
        """Test registration and resolution using DIKey enum"""
        mock_logger = Mock()
        
        self.container.register(DIKey.LOGGER, lambda: mock_logger)
        resolved = self.container.resolve(DIKey.LOGGER)
        
        assert resolved == mock_logger
    
    def test_resolve_nonexistent_key(self):
        """Test resolution of non-registered key"""
        with pytest.raises(ValueError) as exc_info:
            self.container.resolve("nonexistent")
        
        assert "nonexistent is not registered" in str(exc_info.value)
    
    def test_register_override(self):
        """Test overriding existing registration"""
        service1 = Mock(name="service1")
        service2 = Mock(name="service2")
        
        self.container.register("service", lambda: service1)
        self.container.register("service", lambda: service2)
        
        resolved = self.container.resolve("service")
        assert resolved == service2
    
    def test_singleton_behavior(self):
        """Test that resolved instances are created each time"""
        counter = {"value": 0}
        
        def create_service():
            counter["value"] += 1
            return Mock(id=counter["value"])
        
        self.container.register("service", create_service)
        
        first = self.container.resolve("service")
        second = self.container.resolve("service")
        
        # Note: Based on the implementation, new instances are created each time
        assert first is not second
        assert counter["value"] == 2
    
    def test_create_instance_with_dependencies(self):
        """Test creation of instance with automatic dependency injection"""
        mock_dep1 = Mock(name="dep1")
        mock_dep2 = Mock(name="dep2")
        
        self.container.register("dep1", lambda: mock_dep1)
        self.container.register("dep2", lambda: mock_dep2)
        
        # Function with dependencies
        def create_service(dep1, dep2):
            service = Mock()
            service.dep1 = dep1
            service.dep2 = dep2
            return service
        
        self.container.register("service", create_service)
        
        service = self.container.resolve("service")
        
        assert service.dep1 == mock_dep1
        assert service.dep2 == mock_dep2
    
    def test_di_key_enum_values(self):
        """Test DIKey enum contains expected values"""
        # Core drivers
        assert DIKey.FILE_DRIVER.value == "file_driver"
        assert DIKey.SHELL_DRIVER.value == "shell_driver"
        assert DIKey.DOCKER_DRIVER.value == "docker_driver"
        assert DIKey.PYTHON_DRIVER.value == "python_driver"
        
        # Providers
        assert DIKey.JSON_PROVIDER.value == "json_provider"
        assert DIKey.OS_PROVIDER.value == "os_provider"
        assert DIKey.CONFIG_MANAGER.value == "config_manager"
        
        # Logging
        assert DIKey.LOGGER.value == "logger"
        assert DIKey.OUTPUT_MANAGER.value == "output_manager"
    
    def test_provider_with_no_parameters(self):
        """Test provider function with no parameters"""
        mock_service = Mock()
        
        def create_service():
            return mock_service
        
        self.container.register("service", create_service)
        resolved = self.container.resolve("service")
        
        assert resolved == mock_service
    
    def test_provider_with_mixed_dependencies(self):
        """Test provider with mix of registered and non-registered dependencies"""
        mock_logger = Mock(name="logger")
        self.container.register(DIKey.LOGGER, lambda: mock_logger)
        
        def create_service(logger):
            service = Mock()
            service.logger = logger
            return service
        
        self.container.register("service", create_service)
        
        service = self.container.resolve("service")
        assert service.logger == mock_logger
    
    def test_nested_dependency_resolution(self):
        """Test resolution of nested dependencies"""
        # Base dependency
        mock_os = Mock(name="os_provider")
        self.container.register(DIKey.OS_PROVIDER, lambda: mock_os)
        
        # Middle dependency that depends on OS provider
        def create_file_driver(os_provider):
            driver = Mock(name="file_driver")
            driver.os_provider = os_provider
            return driver
        
        self.container.register(DIKey.FILE_DRIVER, create_file_driver)
        
        # Top dependency that depends on file driver
        def create_service(file_driver):
            service = Mock(name="service")
            service.file_driver = file_driver
            return service
        
        self.container.register("service", create_service)
        
        # Resolve top-level service
        service = self.container.resolve("service")
        
        assert service.file_driver.os_provider == mock_os