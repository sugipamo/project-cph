"""Tests for registry provider implementations."""
import pytest

from src.infrastructure.providers.registry_provider import (
    MockRegistryProvider,
    SystemRegistryProvider,
    create_registry_key,
    parse_registry_key,
    validate_registry_name,
)


class TestSystemRegistryProvider:
    """Test SystemRegistryProvider functionality."""

    @pytest.fixture
    def registry_provider(self):
        """Create SystemRegistryProvider instance."""
        return SystemRegistryProvider()

    def test_set_and_get_registry(self, registry_provider):
        """Test setting and getting registry."""
        test_registry = {"key": "value", "number": 42}
        registry_provider.set_registry("test_registry", test_registry)

        retrieved = registry_provider.get_registry("test_registry")
        assert retrieved == test_registry
        assert retrieved is test_registry  # Should be the same object

    def test_get_registry_key_error(self, registry_provider):
        """Test getting non-existent registry raises KeyError."""
        with pytest.raises(KeyError):
            registry_provider.get_registry("nonexistent")

    def test_has_registry_true(self, registry_provider):
        """Test has_registry returns True for existing registry."""
        registry_provider.set_registry("exists", {"data": "test"})
        assert registry_provider.has_registry("exists") is True

    def test_has_registry_false(self, registry_provider):
        """Test has_registry returns False for non-existent registry."""
        assert registry_provider.has_registry("nonexistent") is False

    def test_clear_registry_existing(self, registry_provider):
        """Test clearing existing registry."""
        registry_provider.set_registry("to_clear", {"data": "test"})
        assert registry_provider.has_registry("to_clear") is True

        registry_provider.clear_registry("to_clear")
        assert registry_provider.has_registry("to_clear") is False

    def test_clear_registry_nonexistent(self, registry_provider):
        """Test clearing non-existent registry doesn't raise error."""
        # Should not raise an exception
        registry_provider.clear_registry("nonexistent")
        assert registry_provider.has_registry("nonexistent") is False

    def test_get_all_registries(self, registry_provider):
        """Test getting all registries."""
        registry1 = {"type": "first"}
        registry2 = {"type": "second"}

        registry_provider.set_registry("first", registry1)
        registry_provider.set_registry("second", registry2)

        all_registries = registry_provider.get_all_registries()
        assert len(all_registries) == 2
        assert all_registries["first"] == registry1
        assert all_registries["second"] == registry2

        # Should be a copy, not the original dict
        all_registries["third"] = {"type": "third"}
        assert not registry_provider.has_registry("third")

    def test_clear_all_registries(self, registry_provider):
        """Test clearing all registries."""
        registry_provider.set_registry("first", {"data": "1"})
        registry_provider.set_registry("second", {"data": "2"})

        assert len(registry_provider.get_all_registries()) == 2

        registry_provider.clear_all_registries()
        assert len(registry_provider.get_all_registries()) == 0
        assert not registry_provider.has_registry("first")
        assert not registry_provider.has_registry("second")

    def test_overwrite_registry(self, registry_provider):
        """Test overwriting existing registry."""
        original = {"version": 1}
        updated = {"version": 2}

        registry_provider.set_registry("test", original)
        assert registry_provider.get_registry("test") == original

        registry_provider.set_registry("test", updated)
        assert registry_provider.get_registry("test") == updated
        assert registry_provider.get_registry("test") != original


class TestMockRegistryProvider:
    """Test MockRegistryProvider functionality."""

    @pytest.fixture
    def mock_provider(self):
        """Create MockRegistryProvider instance."""
        return MockRegistryProvider()

    def test_set_and_get_registry_with_logging(self, mock_provider):
        """Test setting and getting registry with access logging."""
        test_registry = {"key": "value"}
        mock_provider.set_registry("test", test_registry)

        retrieved = mock_provider.get_registry("test")
        assert retrieved == test_registry

        # Check access log
        log = mock_provider.get_access_log()
        assert len(log) == 2
        assert log[0] == ("SET", "test")
        assert log[1] == ("GET", "test")

    def test_get_registry_key_error_with_logging(self, mock_provider):
        """Test getting non-existent registry with logging."""
        with pytest.raises(KeyError):
            mock_provider.get_registry("nonexistent")

        # Should still log the access attempt
        log = mock_provider.get_access_log()
        assert len(log) == 1
        assert log[0] == ("GET", "nonexistent")

    def test_has_registry_with_logging(self, mock_provider):
        """Test has_registry with access logging."""
        mock_provider.set_registry("exists", {"data": "test"})

        # Clear log to focus on has_registry calls
        mock_provider.clear_access_log()

        assert mock_provider.has_registry("exists") is True
        assert mock_provider.has_registry("nonexistent") is False

        log = mock_provider.get_access_log()
        assert len(log) == 2
        assert log[0] == ("HAS", "exists")
        assert log[1] == ("HAS", "nonexistent")

    def test_clear_registry_with_logging(self, mock_provider):
        """Test clearing registry with logging."""
        mock_provider.set_registry("to_clear", {"data": "test"})
        mock_provider.clear_access_log()  # Clear setup logs

        mock_provider.clear_registry("to_clear")
        assert not mock_provider.has_registry("to_clear")

        log = mock_provider.get_access_log()
        assert len(log) == 2  # CLEAR and HAS
        assert log[0] == ("CLEAR", "to_clear")
        assert log[1] == ("HAS", "to_clear")

    def test_clear_access_log(self, mock_provider):
        """Test clearing access log."""
        mock_provider.set_registry("test", {"data": "test"})
        assert len(mock_provider.get_access_log()) == 1

        mock_provider.clear_access_log()
        assert len(mock_provider.get_access_log()) == 0

    def test_access_log_independence(self, mock_provider):
        """Test that access log returned is independent copy."""
        mock_provider.set_registry("test", {"data": "test"})

        log1 = mock_provider.get_access_log()
        log2 = mock_provider.get_access_log()

        # Should be equal but not the same object
        assert log1 == log2
        assert log1 is not log2

        # Modifying one shouldn't affect the other
        log1.append(("MODIFIED", "test"))
        assert len(log2) == 1
        assert len(mock_provider.get_access_log()) == 1


class TestRegistryUtilityFunctions:
    """Test utility functions for registry operations."""

    def test_validate_registry_name_valid(self):
        """Test validate_registry_name with valid names."""
        assert validate_registry_name("valid_name") is True
        assert validate_registry_name("valid-name") is True
        assert validate_registry_name("ValidName123") is True
        assert validate_registry_name("test_registry_1") is True
        assert validate_registry_name("a") is True
        assert validate_registry_name("123") is True

    def test_validate_registry_name_invalid(self):
        """Test validate_registry_name with invalid names."""
        assert validate_registry_name("") is False
        assert validate_registry_name("invalid name") is False  # Space
        assert validate_registry_name("invalid@name") is False  # Special char
        assert validate_registry_name("invalid.name") is False  # Dot
        assert validate_registry_name("invalid/name") is False  # Slash
        assert validate_registry_name("invalid:name") is False  # Colon
        assert validate_registry_name(None) is False
        assert validate_registry_name(123) is False  # Not string

    def test_create_registry_key(self):
        """Test create_registry_key function."""
        assert create_registry_key("prefix", "id") == "prefix:id"
        assert create_registry_key("app", "user_123") == "app:user_123"
        assert create_registry_key("", "id") == ":id"
        assert create_registry_key("prefix", "") == "prefix:"

    def test_parse_registry_key_with_colon(self):
        """Test parse_registry_key with colon separator."""
        prefix, identifier = parse_registry_key("app:user_123")
        assert prefix == "app"
        assert identifier == "user_123"

        prefix, identifier = parse_registry_key("complex:key:with:colons")
        assert prefix == "complex"
        assert identifier == "key:with:colons"

    def test_parse_registry_key_without_colon(self):
        """Test parse_registry_key without colon separator."""
        prefix, identifier = parse_registry_key("simple_key")
        assert prefix == "simple_key"
        assert identifier == ""

    def test_parse_registry_key_empty_parts(self):
        """Test parse_registry_key with empty parts."""
        prefix, identifier = parse_registry_key(":identifier")
        assert prefix == ""
        assert identifier == "identifier"

        prefix, identifier = parse_registry_key("prefix:")
        assert prefix == "prefix"
        assert identifier == ""

        prefix, identifier = parse_registry_key(":")
        assert prefix == ""
        assert identifier == ""
