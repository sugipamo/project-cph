"""Tests for registry provider implementations."""
import pytest
from src.infrastructure.registry_provider import (
    SystemRegistryProvider, 
    MockRegistryProvider,
    validate_registry_name,
    create_registry_key,
    parse_registry_key
)


class TestSystemRegistryProvider:
    """Test cases for SystemRegistryProvider."""

    def test_init_creates_empty_registry(self):
        """Test initialization creates empty registry."""
        provider = SystemRegistryProvider()
        assert provider._registries == {}

    def test_set_and_get_registry(self):
        """Test setting and getting registry values."""
        provider = SystemRegistryProvider()
        test_value = {"key": "value"}
        
        provider.set_registry("test_registry", test_value)
        result = provider.get_registry("test_registry")
        
        assert result == test_value

    def test_get_registry_raises_key_error_when_not_found(self):
        """Test get_registry raises KeyError for missing registry."""
        provider = SystemRegistryProvider()
        
        with pytest.raises(KeyError):
            provider.get_registry("nonexistent")

    def test_has_registry_returns_true_when_exists(self):
        """Test has_registry returns True for existing registry."""
        provider = SystemRegistryProvider()
        provider.set_registry("test_registry", "value")
        
        assert provider.has_registry("test_registry") is True

    def test_has_registry_returns_false_when_not_exists(self):
        """Test has_registry returns False for non-existing registry."""
        provider = SystemRegistryProvider()
        
        assert provider.has_registry("nonexistent") is False

    def test_clear_registry_removes_existing(self):
        """Test clear_registry removes existing registry."""
        provider = SystemRegistryProvider()
        provider.set_registry("test_registry", "value")
        
        provider.clear_registry("test_registry")
        
        assert provider.has_registry("test_registry") is False

    def test_clear_registry_handles_non_existing(self):
        """Test clear_registry handles non-existing registry gracefully."""
        provider = SystemRegistryProvider()
        
        # Should not raise exception
        provider.clear_registry("nonexistent")

    def test_get_all_registries_returns_copy(self):
        """Test get_all_registries returns a copy of registries."""
        provider = SystemRegistryProvider()
        provider.set_registry("reg1", "value1")
        provider.set_registry("reg2", "value2")
        
        all_registries = provider.get_all_registries()
        
        assert all_registries == {"reg1": "value1", "reg2": "value2"}
        # Verify it's a copy
        all_registries["reg3"] = "value3"
        assert not provider.has_registry("reg3")

    def test_clear_all_registries(self):
        """Test clear_all_registries removes all registries."""
        provider = SystemRegistryProvider()
        provider.set_registry("reg1", "value1")
        provider.set_registry("reg2", "value2")
        
        provider.clear_all_registries()
        
        assert provider.get_all_registries() == {}


class TestMockRegistryProvider:
    """Test cases for MockRegistryProvider."""

    def test_init_creates_empty_registry_and_log(self):
        """Test initialization creates empty registry and access log."""
        provider = MockRegistryProvider()
        assert provider._registries == {}
        assert provider._access_log == []

    def test_get_registry_logs_access(self):
        """Test get_registry logs access."""
        provider = MockRegistryProvider()
        provider.set_registry("test", "value")
        
        result = provider.get_registry("test")
        
        assert result == "value"
        assert ("GET", "test") in provider.get_access_log()

    def test_set_registry_logs_access(self):
        """Test set_registry logs access."""
        provider = MockRegistryProvider()
        
        provider.set_registry("test", "value")
        
        assert ("SET", "test") in provider.get_access_log()

    def test_has_registry_logs_access(self):
        """Test has_registry logs access."""
        provider = MockRegistryProvider()
        provider.set_registry("test", "value")
        
        result = provider.has_registry("test")
        
        assert result is True
        assert ("HAS", "test") in provider.get_access_log()

    def test_clear_registry_logs_access(self):
        """Test clear_registry logs access."""
        provider = MockRegistryProvider()
        provider.set_registry("test", "value")
        
        provider.clear_registry("test")
        
        assert ("CLEAR", "test") in provider.get_access_log()

    def test_get_access_log_returns_copy(self):
        """Test get_access_log returns a copy."""
        provider = MockRegistryProvider()
        provider.set_registry("test", "value")
        
        log = provider.get_access_log()
        log.append(("FAKE", "entry"))
        
        assert ("FAKE", "entry") not in provider.get_access_log()

    def test_clear_access_log(self):
        """Test clear_access_log empties the log."""
        provider = MockRegistryProvider()
        provider.set_registry("test", "value")
        provider.get_registry("test")
        
        provider.clear_access_log()
        
        assert provider.get_access_log() == []


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def test_validate_registry_name_valid_names(self):
        """Test validate_registry_name with valid names."""
        assert validate_registry_name("test_registry") is True
        assert validate_registry_name("TestRegistry123") is True
        assert validate_registry_name("test-registry") is True
        assert validate_registry_name("TEST_REGISTRY") is True

    def test_validate_registry_name_invalid_names(self):
        """Test validate_registry_name with invalid names."""
        assert validate_registry_name("") is False
        assert validate_registry_name(None) is False
        assert validate_registry_name(123) is False
        assert validate_registry_name("test registry") is False
        assert validate_registry_name("test@registry") is False
        assert validate_registry_name("test.registry") is False

    def test_create_registry_key(self):
        """Test create_registry_key creates formatted key."""
        assert create_registry_key("prefix", "id123") == "prefix:id123"
        assert create_registry_key("system", "config") == "system:config"
        assert create_registry_key("", "id") == ":id"

    def test_parse_registry_key_with_colon(self):
        """Test parse_registry_key with colon separator."""
        assert parse_registry_key("prefix:id123") == ("prefix", "id123")
        assert parse_registry_key("system:config:value") == ("system", "config:value")
        assert parse_registry_key(":id") == ("", "id")

    def test_parse_registry_key_without_colon(self):
        """Test parse_registry_key without colon separator."""
        assert parse_registry_key("simplekey") == ("simplekey", "")
        assert parse_registry_key("") == ("", "")