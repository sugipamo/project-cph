"""Tests for TypeSafeConfigNodeManager"""
import pytest
from unittest.mock import Mock, MagicMock
from pathlib import Path

from src.application.config_manager import (
    TypeSafeConfigNodeManager,
    TypedExecutionConfiguration,
    ConfigurationError,
    FileLoader,
    ConfigValidationError
)
from src.domain.config_node import ConfigNode
from src.configuration.config_resolver import create_config_root_from_dict


class TestTypedExecutionConfiguration:
    """Tests for TypedExecutionConfiguration"""
    
    def test_initialization_with_kwargs(self):
        """Test initialization with keyword arguments"""
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run"
        )
        
        assert config.contest_name == "ABC123"
        assert config.problem_name == "A"
        assert config.language == "python"
        assert config.env_type == "local"
        assert config.command_type == "run"
    
    def test_initialization_with_root_node(self):
        """Test initialization with _root_node"""
        mock_node = Mock(spec=ConfigNode)
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            _root_node=mock_node
        )
        
        assert config.contest_name == "ABC123"
        assert config._root_node == mock_node
    
    def test_resolve_formatted_string_with_root_node(self):
        """Test template resolution with root node"""
        mock_node = Mock(spec=ConfigNode)
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run",
            _root_node=mock_node
        )
        
        # Since resolve_formatted_string is imported from config_resolver,
        # we need to test that it's called correctly
        from unittest.mock import patch, ANY
        with patch('src.application.config_manager.resolve_formatted_string') as mock_resolve:
            mock_resolve.return_value = "resolved_string"
            
            result = config.resolve_formatted_string("template_{contest_name}")
            
            assert result == "resolved_string"
            # Check that it was called with the right args (ANY for regex_ops)
            mock_resolve.assert_called_once_with(
                "template_{contest_name}",
                mock_node,
                {
                    'contest_name': 'ABC123',
                    'problem_name': 'A',
                    'language': 'python',
                    'env_type': 'local',
                    'command_type': 'run'
                },
                ANY  # regex_ops
            )
    
    def test_resolve_formatted_string_without_root_node(self):
        """Test template resolution without root node (fallback)"""
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run",
            local_workspace_path="/workspace",
            timeout_seconds=30,
            language_id="python3",
            source_file_name="main.py",
            run_command="python3 main.py"
        )
        
        # Without root node, it should perform basic string replacement
        result = config.resolve_formatted_string("contest_{contest_name}_problem_{problem_name}")
        assert result == "contest_ABC123_problem_A"
    
    def test_resolve_formatted_string_missing_variable(self):
        """Test template resolution with missing variable"""
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run"
        )
        
        # Should raise ConfigurationError, KeyError, or ValueError for missing template variable
        with pytest.raises((ConfigurationError, KeyError, ValueError)):
            config.resolve_formatted_string("{missing_variable}")
    
    def test_validate_execution_data_valid(self):
        """Test validation with valid data"""
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            problem_name="A",
            language="python",
            env_type="local",
            command_type="run"
        )
        
        is_valid, message = config.validate_execution_data()
        assert is_valid is True
        assert message == ""
    
    def test_validate_execution_data_missing_contest_name(self):
        """Test validation with missing contest name"""
        config = TypedExecutionConfiguration(
            problem_name="A",
            language="python"
        )
        
        is_valid, message = config.validate_execution_data()
        assert is_valid is False
        assert message == "Contest name is required"
    
    def test_validate_execution_data_missing_problem_name(self):
        """Test validation with missing problem name"""
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            language="python"
        )
        
        is_valid, message = config.validate_execution_data()
        assert is_valid is False
        assert message == "Problem name is required"
    
    def test_validate_execution_data_missing_language(self):
        """Test validation with missing language"""
        config = TypedExecutionConfiguration(
            contest_name="ABC123",
            problem_name="A"
        )
        
        is_valid, message = config.validate_execution_data()
        assert is_valid is False
        assert message == "Language is required"
    
    def test_command_type_property(self):
        """Test command_type property getter and setter"""
        config = TypedExecutionConfiguration()
        
        # Test getter when not set
        assert config.command_type is None
        
        # Test setter
        config.command_type = "run"
        assert config.command_type == "run"
    
    def test_dockerfile_resolver_property(self):
        """Test dockerfile_resolver property getter and setter"""
        config = TypedExecutionConfiguration()
        
        # Test getter when not set
        assert config.dockerfile_resolver is None
        
        # Test setter
        mock_resolver = Mock()
        config.dockerfile_resolver = mock_resolver
        assert config.dockerfile_resolver == mock_resolver
    
    def test_get_docker_names_with_resolver(self):
        """Test get_docker_names with dockerfile_resolver"""
        config = TypedExecutionConfiguration(
            language="python"
        )
        
        mock_resolver = Mock()
        mock_resolver.get_docker_names.return_value = {
            'image_name': 'custom-python',
            'container_name': 'custom-python-container'
        }
        config.dockerfile_resolver = mock_resolver
        
        result = config.get_docker_names()
        assert result == {
            'image_name': 'custom-python',
            'container_name': 'custom-python-container'
        }
        mock_resolver.get_docker_names.assert_called_once_with('python')
    
    def test_get_docker_names_without_resolver(self):
        """Test get_docker_names without dockerfile_resolver"""
        config = TypedExecutionConfiguration(
            language="python"
        )
        
        result = config.get_docker_names()
        assert result == {
            'image_name': 'cph-python',
            'container_name': 'cph-python-container',
            'oj_image_name': 'cph-python-oj',
            'oj_container_name': 'cph-python-oj-container'
        }


class TestFileLoader:
    """Tests for FileLoader class"""
    
    @pytest.fixture
    def mock_di_container(self):
        """Create a mock DI container"""
        container = Mock()
        return container
    
    def test_dependency_injection_failure(self, mock_di_container):
        """Test FileLoader when dependency injection fails"""
        # Make resolve throw an exception
        mock_di_container.resolve.side_effect = Exception("Injection failed")
        
        # Should not raise, but providers will be None
        loader = FileLoader(mock_di_container)
        assert loader._json_provider is None
        assert loader._os_provider is None
        assert loader._file_provider is None
    
    def test_get_providers_when_none(self, mock_di_container):
        """Test getting providers when they are None"""
        mock_di_container.resolve.side_effect = Exception("Injection failed")
        loader = FileLoader(mock_di_container)
        
        assert loader._get_json_provider() is None
        assert loader._get_os_provider() is None
        assert loader._get_file_provider() is None
    
    def test_load_system_configs_with_permission_error(self, mock_di_container):
        """Test loading system configs with permission error"""
        mock_file_driver = Mock()
        mock_json_provider = Mock()
        
        def resolve_side_effect(key):
            if key == "file_driver":
                return mock_file_driver
            elif key == "json_provider":
                return mock_json_provider
            return None
        
        mock_di_container.resolve.side_effect = resolve_side_effect
        
        loader = FileLoader(mock_di_container)
        
        # Mock Path object
        mock_path = Mock(spec=Path)
        mock_path.exists.return_value = True
        mock_path.glob.side_effect = PermissionError("Access denied")
        
        with pytest.raises(ConfigurationError, match="システム設定ディレクトリアクセスエラー"):
            loader._load_system_configs(mock_path)
    
    def test_load_language_config_fallback(self, mock_di_container):
        """Test language config loading with fallback"""
        mock_file_driver = Mock()
        mock_json_provider = Mock()
        
        def resolve_side_effect(key):
            if key == "file_driver":
                return mock_file_driver
            elif key == "json_provider":
                return mock_json_provider
            return None
        
        mock_di_container.resolve.side_effect = resolve_side_effect
        
        loader = FileLoader(mock_di_container)
        
        # Use actual Path objects
        from pathlib import Path
        env_path = Path("/test/env")
        
        # Mock file operations - language env.json doesn't exist, but fallback does
        def exists_side_effect(path):
            path_str = str(path)
            # Language-specific env.json doesn't exist
            if path_str == "/test/env/python/env.json":
                return False
            # Fallback python.json exists
            elif path_str == "/test/env/python.json":
                return True
            return False
        
        mock_file_driver.exists.side_effect = exists_side_effect
        
        mock_file_handle = Mock()
        mock_file_handle.read.return_value = '{"test": "value"}'
        mock_file_handle.__enter__ = Mock(return_value=mock_file_handle)
        mock_file_handle.__exit__ = Mock(return_value=None)
        
        def open_side_effect(path, mode='r', encoding='utf-8'):
            # Only open the fallback file
            if str(path) == "/test/env/python.json":
                return mock_file_handle
            raise FileNotFoundError(f"No such file: {path}")
        
        mock_file_driver.open.side_effect = open_side_effect
        
        mock_json_provider.loads.return_value = {"test": "value"}
        
        result = loader._load_language_config(env_path, "python")
        assert result == {"test": "value"}
    
    def test_get_available_languages(self, mock_di_container):
        """Test getting available languages"""
        mock_file_driver = Mock()
        
        def resolve_side_effect(key):
            if key == "file_driver":
                return mock_file_driver
            return None
        
        mock_di_container.resolve.side_effect = resolve_side_effect
        
        loader = FileLoader(mock_di_container)
        
        # Mock path operations
        mock_env_path = Mock(spec=Path)
        mock_env_path.exists.return_value = True
        
        # Mock directory items
        mock_python_dir = Mock(spec=Path)
        mock_python_dir.is_dir.return_value = True
        mock_python_dir.name = "python"
        
        mock_cpp_dir = Mock(spec=Path)
        mock_cpp_dir.is_dir.return_value = True
        mock_cpp_dir.name = "cpp"
        
        mock_shared_dir = Mock(spec=Path)
        mock_shared_dir.is_dir.return_value = True
        mock_shared_dir.name = "shared"  # Should be ignored
        
        mock_file = Mock(spec=Path)
        mock_file.is_dir.return_value = False
        mock_file.name = "config.json"
        
        # Mock env.json existence check
        def mock_div_side_effect(name):
            env_file = Mock(spec=Path)
            if name == "env.json":
                env_file.exists.return_value = True
            return env_file
        
        mock_python_dir.__truediv__ = Mock(side_effect=mock_div_side_effect)
        mock_cpp_dir.__truediv__ = Mock(side_effect=mock_div_side_effect)
        
        mock_env_path.iterdir.return_value = [
            mock_python_dir,
            mock_cpp_dir,
            mock_shared_dir,
            mock_file
        ]
        
        result = loader.get_available_languages(mock_env_path)
        assert result == ["cpp", "python"]  # Sorted
    
    def test_get_available_languages_permission_error(self, mock_di_container):
        """Test getting available languages with permission error"""
        mock_file_driver = Mock()
        
        def resolve_side_effect(key):
            if key == "file_driver":
                return mock_file_driver
            return None
        
        mock_di_container.resolve.side_effect = resolve_side_effect
        
        loader = FileLoader(mock_di_container)
        
        mock_env_path = Mock(spec=Path)
        mock_env_path.exists.return_value = True
        mock_env_path.iterdir.side_effect = PermissionError("Access denied")
        
        with pytest.raises(ConfigurationError, match="言語ディレクトリアクセスエラー"):
            loader.get_available_languages(mock_env_path)
    
    def test_load_json_file_error(self, mock_di_container):
        """Test JSON file loading with error"""
        mock_file_driver = Mock()
        mock_json_provider = Mock()
        
        def resolve_side_effect(key):
            if key == "file_driver":
                return mock_file_driver
            elif key == "json_provider":
                return mock_json_provider
            return None
        
        mock_di_container.resolve.side_effect = resolve_side_effect
        
        loader = FileLoader(mock_di_container)
        
        # File exists but reading fails
        mock_file_driver.exists.return_value = True
        mock_file_driver.open.side_effect = FileNotFoundError("File not found")
        
        with pytest.raises(RuntimeError, match="JSONファイル読み込みエラー"):
            loader.load_json_file("/test/file.json")
    
    def test_load_json_file_no_json_provider(self, mock_di_container):
        """Test JSON file loading when JSON provider is not injected"""
        mock_file_driver = Mock()
        
        def resolve_side_effect(key):
            if key == "file_driver":
                return mock_file_driver
            elif key == "json_provider":
                return None  # No JSON provider
            return None
        
        mock_di_container.resolve.side_effect = resolve_side_effect
        
        loader = FileLoader(mock_di_container)
        
        # File exists
        mock_file_driver.exists.return_value = True
        mock_file_handle = Mock()
        mock_file_handle.read.return_value = '{}'
        mock_file_handle.__enter__ = Mock(return_value=mock_file_handle)
        mock_file_handle.__exit__ = Mock(return_value=None)
        mock_file_driver.open.return_value = mock_file_handle
        
        with pytest.raises(RuntimeError, match="JSONプロバイダーが注入されていません"):
            loader.load_json_file("/test/file.json")


class TestTypeSafeConfigNodeManager:
    """Tests for TypeSafeConfigNodeManager"""
    
    @pytest.fixture
    def mock_di_container(self):
        """Create a mock DI container"""
        container = Mock()
        mock_file_driver = Mock()
        mock_os_provider = Mock()
        mock_json_provider = Mock()
        
        # Set up resolve method to return appropriate mocks
        # Using string keys to avoid infrastructure dependency
        def resolve_side_effect(key):
            if key == "file_driver":
                return mock_file_driver
            elif key == "os_provider":
                return mock_os_provider
            elif key == "json_provider":
                return mock_json_provider
            return None
        
        container.resolve.side_effect = resolve_side_effect
        return container
    
    def test_initialization(self, mock_di_container):
        """Test manager initialization"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        assert manager.infrastructure == mock_di_container
        assert manager.root_node is None
        assert hasattr(manager, 'file_loader')
    
    def test_load_empty_config(self, mock_di_container):
        """Test loading when no config files exist"""
        mock_file_driver = mock_di_container.resolve("file_driver")
        mock_file_driver.exists.return_value = False
        mock_file_driver.read_text.return_value = '{}'
        
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.load_from_files('/system', '/env', 'python')
        
        # Should create root node
        assert manager.root_node is not None
    
    def test_load_with_config_files(self, mock_di_container):
        """Test loading with existing config files"""
        mock_file_driver = mock_di_container.resolve("file_driver")
        mock_os_provider = mock_di_container.resolve("os_provider")
        mock_json_provider = mock_di_container.resolve("json_provider")
        
        # Mock file existence
        mock_file_driver.exists.side_effect = lambda path: True
        
        # Mock file operations
        mock_file_driver.open = Mock()
        mock_file_handle = Mock()
        mock_file_handle.read.return_value = '{"test_key": "test_value"}'
        mock_file_handle.__enter__ = Mock(return_value=mock_file_handle)
        mock_file_handle.__exit__ = Mock(return_value=None)
        mock_file_driver.open.return_value = mock_file_handle
        
        # Mock JSON provider
        mock_json_provider.loads.return_value = {"test_key": "test_value"}
        
        # Mock path operations
        mock_os_provider.path_dirname.return_value = "/test/dir"
        mock_os_provider.path_join.side_effect = lambda *args: "/".join(args)
        mock_os_provider.path_abspath.side_effect = lambda x: x
        
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.load_from_files('/system', '/env', 'python')
        
        assert manager.root_node is not None
    
    def test_resolve_config_simple(self, mock_di_container):
        """Test resolving a simple config value"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Manually set up a root node for testing
        test_data = {"settings": {"debug": True}}
        manager.root_node = create_config_root_from_dict(test_data)
        
        result = manager.resolve_config(['settings', 'debug'], bool)
        assert result is True
    
    def test_resolve_config_not_found(self, mock_di_container):
        """Test resolving non-existent config raises error"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Set up empty root node
        manager.root_node = create_config_root_from_dict({})
        
        with pytest.raises(ValueError):
            manager.resolve_config(['nonexistent', 'key'], str)
    
    def test_resolve_config_not_loaded(self, mock_di_container):
        """Test resolving config before loading raises error"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        with pytest.raises(ConfigurationError, match="Configuration not loaded"):
            manager.resolve_config(['any', 'key'], str)
    
    
    def test_create_execution_config_not_loaded(self, mock_di_container):
        """Test creating execution config before loading raises error"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        with pytest.raises(ConfigurationError, match="Configuration not loaded"):
            manager.create_execution_config(
                contest_name="test",
                problem_name="test",
                language="python",
                env_type="local",
                command_type="run"
            )
    
    def test_initialization_with_none_infrastructure(self):
        """Test initialization with None infrastructure raises error"""
        with pytest.raises(ValueError, match="Infrastructure must be provided"):
            TypeSafeConfigNodeManager(None)
    
    def test_reload_with_language(self, mock_di_container):
        """Test reloading configuration with new language"""
        # Set up mocks
        mock_file_driver = mock_di_container.resolve("file_driver")
        mock_json_provider = mock_di_container.resolve("json_provider")
        
        # Mock file operations
        mock_file_driver.exists.return_value = True
        mock_file_handle = Mock()
        mock_file_handle.read.return_value = '{"test": "value"}'
        mock_file_handle.__enter__ = Mock(return_value=mock_file_handle)
        mock_file_handle.__exit__ = Mock(return_value=None)
        mock_file_driver.open.return_value = mock_file_handle
        
        mock_json_provider.loads.return_value = {"test": "value"}
        
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Initial load
        manager.load_from_files('/system', '/env', 'python')
        
        # Reload with new language
        manager.reload_with_language('cpp')
        
        assert manager._language == 'cpp'
        assert manager.root_node is not None
    
    def test_reload_with_language_not_initialized(self, mock_di_container):
        """Test reloading before initial load raises error"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        with pytest.raises(ConfigurationError, match="Initial configuration not loaded"):
            manager.reload_with_language('cpp')
    
    def test_resolve_config_with_caching(self, mock_di_container):
        """Test config resolution uses caching"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Set up root node
        test_data = {"settings": {"timeout": 30}}
        manager.root_node = create_config_root_from_dict(test_data)
        
        # First call should populate cache
        result1 = manager.resolve_config(['settings', 'timeout'], int)
        assert result1 == 30
        
        # Second call should use cache (modify root_node to verify)
        manager.root_node = create_config_root_from_dict({"settings": {"timeout": 60}})
        result2 = manager.resolve_config(['settings', 'timeout'], int)
        assert result2 == 30  # Should still be cached value
    
    def test_resolve_config_list(self, mock_di_container):
        """Test resolving list configuration"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        test_data = {"languages": ["python", "cpp", "java"]}
        manager.root_node = create_config_root_from_dict(test_data)
        
        result = manager.resolve_config_list(['languages'], str)
        assert result == ["python", "cpp", "java"]
    
    def test_resolve_config_list_not_found(self, mock_di_container):
        """Test resolving non-existent list raises error"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        with pytest.raises((KeyError, ValueError)):
            manager.resolve_config_list(['nonexistent'], str)
    
    def test_resolve_config_list_not_list(self, mock_di_container):
        """Test resolving non-list value raises error"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        test_data = {"value": "not_a_list"}
        manager.root_node = create_config_root_from_dict(test_data)
        
        with pytest.raises(TypeError, match="Expected list, got"):
            manager.resolve_config_list(['value'], str)
    
    def test_resolve_template_typed(self, mock_di_container):
        """Test typed template resolution"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        test_data = {"timeout": 30}
        manager.root_node = create_config_root_from_dict(test_data)
        
        from unittest.mock import patch
        with patch('src.application.config_manager.resolve_formatted_string') as mock_resolve:
            mock_resolve.return_value = "30"
            
            result = manager.resolve_template_typed("{timeout}", {"test": "value"}, int)
            assert result == 30
            
            # Verify resolve_formatted_string was called with correct args
            assert mock_resolve.call_count == 1
    
    def test_resolve_template_typed_with_cache(self, mock_di_container):
        """Test template resolution uses caching"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        from unittest.mock import patch
        with patch('src.application.config_manager.resolve_formatted_string') as mock_resolve:
            mock_resolve.return_value = "cached_value"
            
            # First call
            result1 = manager.resolve_template_typed("{test}", {"key": "value"}, str)
            assert result1 == "cached_value"
            assert mock_resolve.call_count == 1
            
            # Second call with same parameters should use cache
            result2 = manager.resolve_template_typed("{test}", {"key": "value"}, str)
            assert result2 == "cached_value"
            assert mock_resolve.call_count == 1  # Should not increase
    
    def test_resolve_template_typed_none_context(self, mock_di_container):
        """Test template resolution with None context raises error"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        with pytest.raises(ValueError, match="context cannot be None"):
            manager.resolve_template_typed("{test}", None, str)
    
    def test_resolve_template_to_path(self, mock_di_container):
        """Test template resolution to Path"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        from unittest.mock import patch
        with patch.object(manager, 'resolve_template_typed') as mock_resolve:
            mock_resolve.return_value = "/test/path"
            
            result = manager.resolve_template_to_path("{workspace}/test", {"workspace": "/home"})
            assert isinstance(result, Path)
            assert str(result) == "/test/path"
    
    def test_validate_template_success(self, mock_di_container):
        """Test template validation success"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        from unittest.mock import patch
        with patch.object(manager, 'resolve_template_typed') as mock_resolve:
            mock_resolve.return_value = "valid"
            
            result = manager.validate_template("{test}")
            assert result is True
    
    def test_validate_template_failure(self, mock_di_container):
        """Test template validation failure"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        from unittest.mock import patch
        with patch.object(manager, 'resolve_template_typed') as mock_resolve:
            mock_resolve.side_effect = KeyError("Invalid template")
            
            with pytest.raises(ValueError, match="Template validation failed"):
                manager.validate_template("{invalid}")
    
    def test_resolve_config_validated_success(self, mock_di_container):
        """Test config resolution with validation success"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        test_data = {"port": 8080}
        manager.root_node = create_config_root_from_dict(test_data)
        
        # Validator that checks port is in valid range
        def validator(port):
            return 1 <= port <= 65535
        
        result = manager.resolve_config_validated(
            ['port'], int, validator, "Invalid port number"
        )
        assert result == 8080
    
    def test_resolve_config_validated_failure(self, mock_di_container):
        """Test config resolution with validation failure"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        test_data = {"port": 99999}
        manager.root_node = create_config_root_from_dict(test_data)
        
        # Validator that checks port is in valid range
        def validator(port):
            return 1 <= port <= 65535
        
        from src.application.config_manager import ConfigValidationError
        with pytest.raises(ConfigValidationError, match="Invalid port number"):
            manager.resolve_config_validated(
                ['port'], int, validator, "Invalid port number"
            )
    
    def test_resolve_timeout_with_fallbacks(self, mock_di_container):
        """Test timeout resolution with multiple fallback paths"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Test with timeout in nested path
        test_data = {"python": {"timeout": 45}}
        manager.root_node = create_config_root_from_dict(test_data)
        
        result = manager._resolve_timeout_with_fallbacks()
        assert result == 45
    
    def test_resolve_timeout_with_fallbacks_not_found(self, mock_di_container):
        """Test timeout resolution when no path has value"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        with pytest.raises(ConfigurationError, match="タイムアウト値の取得に失敗しました"):
            manager._resolve_timeout_with_fallbacks()
    
    def test_create_execution_config_basic(self, mock_di_container):
        """Test creating basic execution configuration"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Set up comprehensive test data with all required paths
        test_data = {
            "paths": {
                "local_workspace_path": "/workspace",
                "contest_current_path": "{workspace}/current/{contest_name}",
                "contest_stock_path": "{workspace}/stock/{contest_name}",
                "contest_template_path": "{workspace}/template",
                "contest_temp_path": "{workspace}/temp/{contest_name}"
            },
            "workspace": "/workspace",  # Add fallback workspace
            "timeout": {"default": 30},
            "python": {
                "language_id": "python3",
                "source_file_name": "main.py",
                "run_command": "python3 {source_file_name}"
            },
            "debug": False,
            "shared": {"debug": False}  # Add fallback debug
        }
        manager.root_node = create_config_root_from_dict(test_data)
        
        # Mock the regex provider
        from unittest.mock import patch
        with patch('src.utils.regex_provider.RegexProvider'):
            config = manager.create_execution_config(
                contest_name="ABC123",
                problem_name="A",
                language="python",
                env_type="local",
                command_type="run"
            )
        
        assert config.contest_name == "ABC123"
        assert config.problem_name == "A"
        assert config.language == "python"
        assert config.env_type == "local"
        assert config.command_type == "run"
        assert config.timeout_seconds == 30
        assert config.language_id == "python3"
        assert config.source_file_name == "main.py"
        assert config.run_command == "python3 {source_file_name}"
        assert config.debug_mode is False
    
    def test_create_execution_config_with_cache(self, mock_di_container):
        """Test execution config caching"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        test_data = {
            "paths": {
                "local_workspace_path": "/workspace",
                "contest_current_path": "{workspace}/current/{contest_name}",
                "contest_stock_path": "{workspace}/stock/{contest_name}",
                "contest_template_path": "{workspace}/template",
                "contest_temp_path": "{workspace}/temp/{contest_name}"
            },
            "workspace": "/workspace",
            "timeout": {"default": 30},
            "python": {
                "language_id": "python3",
                "source_file_name": "main.py",
                "run_command": "python3 main.py"
            },
            "shared": {"debug": False}
        }
        manager.root_node = create_config_root_from_dict(test_data)
        
        # Mock the regex provider
        from unittest.mock import patch
        with patch('src.utils.regex_provider.RegexProvider'):
            # Create config twice with same parameters
            config1 = manager.create_execution_config(
                "ABC123", "A", "python", "local", "run"
            )
            config2 = manager.create_execution_config(
                "ABC123", "A", "python", "local", "run"
            )
        
        # Should be the same object (cached)
        assert config1 is config2
    
    def test_resolve_workspace_path_not_found(self, mock_di_container):
        """Test workspace path resolution when not found"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        with pytest.raises(KeyError, match="ワークスペースパスの設定が見つかりません"):
            manager._resolve_workspace_path()
    
    def test_resolve_debug_mode_multiple_paths(self, mock_di_container):
        """Test debug mode resolution with fallback paths"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Debug mode in shared config
        test_data = {"shared": {"debug": True}}
        manager.root_node = create_config_root_from_dict(test_data)
        
        result = manager._resolve_debug_mode()
        assert result is True
    
    def test_resolve_debug_mode_not_found(self, mock_di_container):
        """Test debug mode resolution when not found"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        manager.root_node = create_config_root_from_dict({})
        
        with pytest.raises(ConfigurationError, match="デバッグモード設定の取得に失敗しました"):
            manager._resolve_debug_mode()
    
    def test_convert_to_type_string(self, mock_di_container):
        """Test type conversion to string"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        assert manager._convert_to_type(123, str) == "123"
        assert manager._convert_to_type(True, str) == "True"
        assert manager._convert_to_type("test", str) == "test"
    
    def test_convert_to_type_int(self, mock_di_container):
        """Test type conversion to int"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        assert manager._convert_to_type("123", int) == 123
        assert manager._convert_to_type(123.0, int) == 123
        
        # Bool to int should raise error
        with pytest.raises(TypeError, match="Cannot convert bool to int"):
            manager._convert_to_type(True, int)
    
    def test_convert_to_type_bool(self, mock_di_container):
        """Test type conversion to bool"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Direct bool
        assert manager._convert_to_type(True, bool) is True
        assert manager._convert_to_type(False, bool) is False
        
        # String to bool
        assert manager._convert_to_type("true", bool) is True
        assert manager._convert_to_type("TRUE", bool) is True
        assert manager._convert_to_type("1", bool) is True
        assert manager._convert_to_type("yes", bool) is True
        assert manager._convert_to_type("on", bool) is True
        
        assert manager._convert_to_type("false", bool) is False
        assert manager._convert_to_type("FALSE", bool) is False
        assert manager._convert_to_type("0", bool) is False
        assert manager._convert_to_type("no", bool) is False
        assert manager._convert_to_type("off", bool) is False
        
        # Invalid bool conversion
        with pytest.raises(TypeError, match="Cannot convert .* to bool"):
            manager._convert_to_type("invalid", bool)
    
    def test_convert_to_type_float(self, mock_di_container):
        """Test type conversion to float"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        assert manager._convert_to_type("123.45", float) == 123.45
        assert manager._convert_to_type(123, float) == 123.0
    
    def test_convert_to_type_path(self, mock_di_container):
        """Test type conversion to Path"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        result = manager._convert_to_type("/test/path", Path)
        assert isinstance(result, Path)
        assert str(result) == "/test/path"
    
    def test_convert_to_type_invalid(self, mock_di_container):
        """Test type conversion with invalid type"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        # Custom type that doesn't match
        class CustomType:
            pass
        
        with pytest.raises(TypeError, match="Expected .*, got"):
            manager._convert_to_type("test", CustomType)
    
    def test_cache_overflow(self, mock_di_container):
        """Test cache overflow handling"""
        manager = TypeSafeConfigNodeManager(mock_di_container)
        
        test_data = {
            "paths": {
                "local_workspace_path": "/workspace",
                "contest_current_path": "{workspace}/current/{contest_name}",
                "contest_stock_path": "{workspace}/stock/{contest_name}",
                "contest_template_path": "{workspace}/template",
                "contest_temp_path": "{workspace}/temp/{contest_name}"
            },
            "workspace": "/workspace", 
            "timeout": {"default": 30},
            "python": {
                "language_id": "python3",
                "source_file_name": "main.py",
                "run_command": "python3 main.py"
            },
            "shared": {"debug": False}
        }
        manager.root_node = create_config_root_from_dict(test_data)
        
        # Mock the regex provider
        from unittest.mock import patch
        with patch('src.utils.regex_provider.RegexProvider'):
            # Fill cache beyond limit
            for i in range(1002):
                config = manager.create_execution_config(
                    f"ABC{i}", "A", "python", "local", "run"
                )
        
        # Cache should not exceed 1000
        assert len(manager._execution_config_cache) <= 1000
    
