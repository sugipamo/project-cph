"""Tests for DI container adapter"""
import pytest
from unittest.mock import Mock, MagicMock
from src.infrastructure.di_container_adapter import DIContainerAdapter
from src.infrastructure.di_container import DIContainer, DIKey


class TestDIContainerAdapter:
    """Test cases for DIContainerAdapter"""

    @pytest.fixture
    def mock_container(self):
        """Create mock DIContainer"""
        return Mock(spec=DIContainer)

    @pytest.fixture
    def adapter(self, mock_container):
        """Create DIContainerAdapter with mock container"""
        return DIContainerAdapter(mock_container)

    def test_init(self, mock_container):
        """Test adapter initialization"""
        adapter = DIContainerAdapter(mock_container)
        assert adapter._container is mock_container

    def test_resolve_with_dikey_enum_member(self, adapter, mock_container):
        """Test resolving with string that matches DIKey enum member"""
        # Mock the container's resolve method
        expected_result = Mock()
        mock_container.resolve.return_value = expected_result
        
        # Test with a string that matches a DIKey enum member
        result = adapter.resolve("json_provider")
        
        # Verify it was converted to enum and resolved
        mock_container.resolve.assert_called_once_with(DIKey.JSON_PROVIDER)
        assert result is expected_result

    def test_resolve_with_uppercase_dikey(self, adapter, mock_container):
        """Test resolving with uppercase string matching DIKey"""
        expected_result = Mock()
        mock_container.resolve.return_value = expected_result
        
        # Test with uppercase string
        result = adapter.resolve("FILE_DRIVER")
        
        # Verify it was converted to enum and resolved
        mock_container.resolve.assert_called_once_with(DIKey.FILE_DRIVER)
        assert result is expected_result

    def test_resolve_with_mixed_case_dikey(self, adapter, mock_container):
        """Test resolving with mixed case string matching DIKey"""
        expected_result = Mock()
        mock_container.resolve.return_value = expected_result
        
        # Test with mixed case
        result = adapter.resolve("JsOn_PrOvIdEr")
        
        # Verify it was converted to enum and resolved
        mock_container.resolve.assert_called_once_with(DIKey.JSON_PROVIDER)
        assert result is expected_result

    def test_resolve_with_non_dikey_string(self, adapter, mock_container):
        """Test resolving with string that doesn't match any DIKey"""
        expected_result = Mock()
        mock_container.resolve.return_value = expected_result
        
        # Test with string that's not a DIKey member
        result = adapter.resolve("custom_service")
        
        # Verify it was passed as string directly
        mock_container.resolve.assert_called_once_with("custom_service")
        assert result is expected_result

    def test_resolve_propagates_exception(self, adapter, mock_container):
        """Test that exceptions from container are propagated"""
        mock_container.resolve.side_effect = KeyError("Dependency not found")
        
        with pytest.raises(KeyError) as exc_info:
            adapter.resolve("unknown_key")
        
        assert "Dependency not found" in str(exc_info.value)

    def test_resolve_with_all_known_dikeys(self, adapter, mock_container):
        """Test resolving all known DIKey enum values"""
        # Get all DIKey enum members
        dikey_members = [
            "JSON_PROVIDER",
            "SQLITE_PROVIDER",
            "OS_PROVIDER",
            "DOCKER_DRIVER",
            "FILE_DRIVER",
            "SHELL_DRIVER",
            "PYTHON_DRIVER",
            "SYS_PROVIDER"
        ]
        
        for key_string in dikey_members:
            mock_container.reset_mock()
            mock_result = Mock()
            mock_container.resolve.return_value = mock_result
            
            # Test both lowercase and original case
            result = adapter.resolve(key_string.lower())
            
            # Verify enum was used
            expected_enum = DIKey[key_string]
            mock_container.resolve.assert_called_once_with(expected_enum)
            assert result is mock_result

    def test_adapter_implements_interface(self):
        """Test that adapter implements DIContainerInterface"""
        from src.operations.interfaces.utility_interfaces import DIContainerInterface
        
        mock_container = Mock(spec=DIContainer)
        adapter = DIContainerAdapter(mock_container)
        
        # Verify it has the required interface method
        assert hasattr(adapter, 'resolve')
        assert callable(adapter.resolve)
        
        # While we can't check isinstance with Protocol in runtime,
        # we can verify the method signature matches
        import inspect
        sig = inspect.signature(adapter.resolve)
        assert 'key' in sig.parameters
        assert sig.parameters['key'].annotation == str