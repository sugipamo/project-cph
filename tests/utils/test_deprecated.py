"""Tests for deprecated decorator utility"""
import warnings

import pytest

from src.utils.deprecated import deprecated


class TestDeprecatedDecorator:
    """Test suite for deprecated decorator"""

    def test_deprecated_function_basic(self):
        """Test deprecated decorator on a function shows warning"""
        @deprecated("Use new_function instead")
        def old_function():
            return "old result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_function is deprecated" in str(w[0].message)
            assert "Use new_function instead" in str(w[0].message)
            assert result == "old result"

    def test_deprecated_function_with_args(self):
        """Test deprecated decorator on function with arguments"""
        @deprecated("This function is obsolete")
        def old_function_with_args(x, y, z=None):
            return x + y + (z or 0)

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = old_function_with_args(1, 2, z=3)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_function_with_args is deprecated" in str(w[0].message)
            assert "This function is obsolete" in str(w[0].message)
            assert result == 6

    def test_deprecated_function_preserves_metadata(self):
        """Test deprecated decorator preserves function metadata"""
        @deprecated("Use new_version instead")
        def documented_function():
            """This is a documented function."""
            return "result"

        assert documented_function.__name__ == "documented_function"
        assert documented_function.__doc__ == "This is a documented function."

    def test_deprecated_class_basic(self):
        """Test deprecated decorator on a class shows warning during instantiation"""
        @deprecated("Use NewClass instead")
        class OldClass:
            def __init__(self, value):
                self.value = value

            def get_value(self):
                return self.value

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            instance = OldClass("test")

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "OldClass is deprecated" in str(w[0].message)
            assert "Use NewClass instead" in str(w[0].message)
            assert instance.value == "test"
            assert instance.get_value() == "test"

    def test_deprecated_class_multiple_instances(self):
        """Test deprecated decorator shows warning for each class instantiation"""
        @deprecated("This class is old")
        class OldClass:
            def __init__(self):
                pass

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            OldClass()
            OldClass()

            assert len(w) == 2
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)
                assert "OldClass is deprecated" in str(warning.message)

    def test_deprecated_class_with_args(self):
        """Test deprecated decorator on class with __init__ arguments"""
        @deprecated("Use ModernClass instead")
        class OldClassWithArgs:
            def __init__(self, name, age=0):
                self.name = name
                self.age = age

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            instance = OldClassWithArgs("Alice", age=25)

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert instance.name == "Alice"
            assert instance.age == 25

    def test_deprecated_method_in_class(self):
        """Test deprecated decorator on individual methods"""
        class TestClass:
            @deprecated("Use new_method instead")
            def old_method(self):
                return "old method result"

            def new_method(self):
                return "new method result"

        instance = TestClass()

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = instance.old_method()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert "old_method is deprecated" in str(w[0].message)
            assert result == "old method result"

        # New method should not trigger warning
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = instance.new_method()

            assert len(w) == 0
            assert result == "new method result"

    def test_deprecated_static_method(self):
        """Test deprecated decorator on static methods"""
        class TestClass:
            @staticmethod
            @deprecated("Use new_static_method instead")
            def old_static_method():
                return "static result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = TestClass.old_static_method()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert result == "static result"

    def test_deprecated_class_method(self):
        """Test deprecated decorator on class methods"""
        class TestClass:
            @classmethod
            @deprecated("Use new_class_method instead")
            def old_class_method(cls):
                return "class method result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = TestClass.old_class_method()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert result == "class method result"

    def test_deprecated_function_exception_handling(self):
        """Test deprecated decorator when decorated function raises exception"""
        @deprecated("This function raises errors")
        def error_function():
            raise ValueError("Test error")

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            with pytest.raises(ValueError, match="Test error"):
                error_function()

            # Warning should still be shown even if function raises exception
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)

    def test_deprecated_class_inheritance(self):
        """Test deprecated decorator on inherited class"""
        @deprecated("BaseClass is deprecated")
        class BaseClass:
            def __init__(self):
                self.base_value = "base"

        class DerivedClass(BaseClass):
            def __init__(self):
                super().__init__()
                self.derived_value = "derived"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            instance = DerivedClass()

            # Should trigger warning from base class __init__
            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            assert instance.base_value == "base"
            assert instance.derived_value == "derived"

    def test_deprecated_multiple_calls_same_function(self):
        """Test deprecated decorator shows warning on each function call"""
        @deprecated("Function is obsolete")
        def repeated_function():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")

            repeated_function()
            repeated_function()
            repeated_function()

            assert len(w) == 3
            for warning in w:
                assert issubclass(warning.category, DeprecationWarning)
                assert "repeated_function is deprecated" in str(warning.message)

    def test_deprecated_empty_message(self):
        """Test deprecated decorator with empty message"""
        @deprecated("")
        def function_with_empty_message():
            return "result"

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            result = function_with_empty_message()

            assert len(w) == 1
            assert issubclass(w[0].category, DeprecationWarning)
            # Should still contain function name and basic message
            assert "function_with_empty_message is deprecated" in str(w[0].message)
            assert result == "result"
