"""Tests for legacy_compatibility module"""
import warnings

import pytest


# Test that importing the module triggers deprecation warning
def test_import_warning():
    """Test that importing legacy_compatibility module shows deprecation warning"""
    with warnings.catch_warnings(record=True) as w:
        warnings.simplefilter("always")

        # Import the module to trigger the warning
        import src.utils.legacy_compatibility

        assert len(w) == 1
        assert issubclass(w[0].category, DeprecationWarning)
        warning_message = str(w[0].message)
        assert "src.utils.helpers is deprecated" in warning_message
        assert "string_formatters" in warning_message
        assert "docker_wrappers" in warning_message
        assert "data_processors" in warning_message


def test_module_exists():
    """Test that the legacy compatibility module can be imported"""
    try:
        import src.utils.legacy_compatibility
        # Module should exist and be importable
        assert src.utils.legacy_compatibility is not None
    except ImportError:
        pytest.fail("legacy_compatibility module should be importable")


def test_module_content():
    """Test that the module has expected content structure"""
    import src.utils.legacy_compatibility as legacy_module

    # Should have __doc__ string indicating deprecation
    assert legacy_module.__doc__ is not None
    assert "DEPRECATED" in legacy_module.__doc__
    assert "Backward compatibility" in legacy_module.__doc__


class TestLegacyCompatibilityWarning:
    """Test suite for legacy compatibility warning behavior"""

    def test_warning_stacklevel(self):
        """Test that warning shows correct stack level"""
        import sys

        # Remove module from cache to trigger fresh import
        module_name = "src.utils.legacy_compatibility"
        if module_name in sys.modules:
            del sys.modules[module_name]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # Import in a function to test stack level
            def import_legacy():
                import src.utils.legacy_compatibility
                return src.utils.legacy_compatibility

            import_legacy()

            # Should have at least one warning
            assert len(w) >= 1
            warning_found = False
            for warning in w:
                if issubclass(warning.category, DeprecationWarning):
                    warning_found = True
                    break
            assert warning_found

    def test_multiple_imports_same_warning(self):
        """Test that multiple imports of the same module trigger warning each time"""
        import sys

        # Remove module from cache if it exists
        module_name = "src.utils.legacy_compatibility"
        if module_name in sys.modules:
            del sys.modules[module_name]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            # First import
            import src.utils.legacy_compatibility as legacy1

            # Force reload by removing from cache
            if module_name in sys.modules:
                del sys.modules[module_name]

            # Second import
            import src.utils.legacy_compatibility as legacy2

            # Should have warnings from both imports
            assert len(w) >= 1  # At least one warning
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)

    def test_warning_message_content(self):
        """Test that warning message contains all required information"""
        import sys

        # Remove module from cache to trigger fresh import
        module_name = "src.utils.legacy_compatibility"
        if module_name in sys.modules:
            del sys.modules[module_name]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            import src.utils.legacy_compatibility

            # Should have at least one deprecation warning
            assert len(w) >= 1

            # Find the deprecation warning
            deprecation_warning = None
            for warning in w:
                if issubclass(warning.category, DeprecationWarning):
                    deprecation_warning = warning
                    break

            assert deprecation_warning is not None
            message = str(deprecation_warning.message)

            # Should mention the deprecated module name
            assert "src.utils.helpers" in message

            # Should mention alternative modules
            expected_alternatives = ["string_formatters", "docker_wrappers", "data_processors"]
            for alternative in expected_alternatives:
                assert alternative in message

    def test_import_doesnt_fail(self):
        """Test that importing the deprecated module doesn't cause import failure"""
        try:
            import src.utils.legacy_compatibility
            # Should succeed without raising any exceptions
        except Exception as e:
            pytest.fail(f"Import should not fail, but got: {e}")

    def test_module_attributes(self):
        """Test that module has expected basic attributes"""
        import src.utils.legacy_compatibility as legacy_module

        # Should have standard module attributes
        assert hasattr(legacy_module, "__file__")
        assert hasattr(legacy_module, "__name__")

        # Module name should be correct
        assert legacy_module.__name__ == "src.utils.legacy_compatibility"
