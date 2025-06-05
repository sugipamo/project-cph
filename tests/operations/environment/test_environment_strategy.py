"""
Test environment strategy pattern implementation
"""
import pytest
from src.operations.environment.base_strategy import EnvironmentStrategy
from src.operations.environment.local_strategy import LocalStrategy
from src.operations.environment.docker_strategy import DockerStrategy
from src.operations.environment.strategy_registry import (
    EnvironmentStrategyRegistry, get_strategy, get_default_strategy
)
from src.operations.environment.environment_manager import EnvironmentManager
from src.operations.result.result import OperationResult


class TestEnvironmentStrategy:
    
    def test_local_strategy(self):
        """Test LocalStrategy implementation"""
        strategy = LocalStrategy()
        
        assert strategy.name == "local"
        assert "host" in strategy.aliases
        assert "native" in strategy.aliases
        
        # Test matching
        assert strategy.matches("local")
        assert strategy.matches("host")
        assert not strategy.matches("docker")
        
        # Test environment preparation
        result = strategy.prepare_environment(None)
        assert result.success
        assert "ready" in result.stdout
        
        # Test cleanup
        result = strategy.cleanup_environment(None)
        assert result.success
        
        # Test force local (always false for local)
        assert not strategy.should_force_local({})
        assert not strategy.should_force_local({'force_env_type': 'local'})
    
    def test_docker_strategy(self):
        """Test DockerStrategy implementation"""
        config = {
            'working_directory': '/workspace',
            'mount_path': '/workspace',
        }
        strategy = DockerStrategy(config)
        
        assert strategy.name == "docker"
        assert "container" in strategy.aliases
        assert "isolated" in strategy.aliases
        
        # Test matching
        assert strategy.matches("docker")
        assert strategy.matches("container")
        assert not strategy.matches("local")
        
        # Test configuration
        assert strategy.get_working_directory() == "/workspace"
        assert strategy.get_mount_path() == "/workspace"
        
        # Test force local detection
        assert not strategy.should_force_local({})
        assert strategy.should_force_local({'force_env_type': 'local'})
        assert not strategy.should_force_local({'force_env_type': 'docker'})
    
    def test_strategy_registry(self):
        """Test EnvironmentStrategyRegistry"""
        registry = EnvironmentStrategyRegistry()
        
        # Test getting strategies
        local = registry.get_strategy("local")
        assert local is not None
        assert isinstance(local, LocalStrategy)
        
        docker = registry.get_strategy("docker")
        assert docker is not None
        assert isinstance(docker, DockerStrategy)
        
        # Test aliases
        assert registry.get_strategy("host") is local
        assert registry.get_strategy("container") is docker
        
        # Test default strategy
        default = registry.get_default_strategy()
        assert default is not None
        assert default.name == "local"
        
        # Test setting default
        registry.set_default_strategy("docker")
        assert registry.get_default_strategy().name == "docker"
        
        # Test getting all strategies
        all_strategies = registry.get_all_strategies()
        assert len(all_strategies) >= 2
        names = [s.name for s in all_strategies]
        assert "local" in names
        assert "docker" in names
    
    def test_global_registry_functions(self):
        """Test global registry functions"""
        # Test get_strategy
        local = get_strategy("local")
        assert local is not None
        assert isinstance(local, LocalStrategy)
        
        # Test get_default_strategy
        default = get_default_strategy()
        assert default is not None
    
    def test_environment_manager(self):
        """Test EnvironmentManager"""
        # Test with explicit env_type
        manager = EnvironmentManager("docker")
        assert manager.strategy.name == "docker"
        
        # Test with default
        manager = EnvironmentManager()
        assert manager.strategy is not None
        
        # Test strategy switching
        manager.switch_strategy("local")
        assert manager.strategy.name == "local"
        
        # Test invalid strategy
        with pytest.raises(ValueError):
            manager.switch_strategy("invalid")
        
        # Test working directory
        wd = manager.get_working_directory()
        assert wd == "."  # Local default
        
        # Test from context
        class MockContext:
            env_type = "docker"
        
        manager = EnvironmentManager.from_context(MockContext())
        assert manager.strategy.name == "docker"
    
    def test_strategy_config_update(self):
        """Test updating strategy configuration"""
        from src.operations.environment.strategy_registry import update_strategy_config
        
        # Update docker config
        new_config = {
            'working_directory': '/app',
            'timeout_seconds': 600,
        }
        update_strategy_config('docker', new_config)
        
        # Verify update
        docker = get_strategy('docker')
        assert docker.get_working_directory() == '/app'
        assert docker.get_timeout() == 600