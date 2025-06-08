"""Tests for base command pattern implementation"""

from typing import Any, Optional

import pytest

from src.context.commands.base_command import Command


class ConcreteTestCommand(Command):
    """Concrete implementation of Command for testing"""

    def __init__(self, name: str = "test", aliases: Optional[list[str]] = None, description: str = "Test command"):
        super().__init__()
        self._name = name
        self._aliases = aliases or []
        self._description = description

    @property
    def name(self) -> str:
        return self._name

    def validate(self, context: Any) -> tuple[bool, Optional[str]]:
        # Simple validation for testing
        if context is None:
            return False, "Context cannot be None"
        return True, None

    def get_steps(self, context: Any) -> list[dict[str, Any]]:
        return [{"type": "test", "cmd": ["echo", "test"]}]


class TestCommandClass:
    """Test cases for Command abstract base class"""

    def test_command_initialization(self):
        """Test command initialization"""
        cmd = ConcreteTestCommand()

        assert cmd.name == "test"
        assert cmd.aliases == []
        assert cmd.description == "Test command"

    def test_command_with_aliases(self):
        """Test command with aliases"""
        aliases = ["t", "tst"]
        cmd = ConcreteTestCommand(aliases=aliases)

        assert cmd.aliases == aliases

    def test_command_with_custom_description(self):
        """Test command with custom description"""
        description = "Custom test command"
        cmd = ConcreteTestCommand(description=description)

        assert cmd.description == description

    def test_command_properties(self):
        """Test command properties"""
        cmd = ConcreteTestCommand(
            name="custom",
            aliases=["c", "cust"],
            description="Custom command"
        )

        assert cmd.name == "custom"
        assert cmd.aliases == ["c", "cust"]
        assert cmd.description == "Custom command"

    def test_validate_success(self):
        """Test successful validation"""
        cmd = ConcreteTestCommand()
        context = {"test": "data"}

        is_valid, error = cmd.validate(context)

        assert is_valid
        assert error is None

    def test_validate_failure(self):
        """Test validation failure"""
        cmd = ConcreteTestCommand()
        context = None

        is_valid, error = cmd.validate(context)

        assert not is_valid
        assert error == "Context cannot be None"

    def test_get_steps(self):
        """Test get_steps method"""
        cmd = ConcreteTestCommand()
        context = {"test": "data"}

        steps = cmd.get_steps(context)

        assert len(steps) == 1
        assert steps[0]["type"] == "test"
        assert steps[0]["cmd"] == ["echo", "test"]

    def test_matches_exact_name(self):
        """Test matches method with exact name"""
        cmd = ConcreteTestCommand(name="deploy")

        assert cmd.matches("deploy")
        assert not cmd.matches("test")

    def test_matches_alias(self):
        """Test matches method with aliases"""
        cmd = ConcreteTestCommand(name="deploy", aliases=["d", "dep"])

        assert cmd.matches("deploy")
        assert cmd.matches("d")
        assert cmd.matches("dep")
        assert not cmd.matches("other")

    def test_matches_case_sensitive(self):
        """Test matches method is case sensitive"""
        cmd = ConcreteTestCommand(name="deploy", aliases=["D"])

        assert not cmd.matches("Deploy")
        assert not cmd.matches("d")
        assert cmd.matches("D")

    def test_matches_empty_aliases(self):
        """Test matches method with empty aliases"""
        cmd = ConcreteTestCommand(name="test")

        assert cmd.matches("test")
        assert not cmd.matches("other")

    def test_abstract_methods_required(self):
        """Test that abstract methods are required"""
        with pytest.raises(TypeError):
            Command()  # Should fail because it's abstract

    def test_command_inheritance(self):
        """Test command inheritance"""
        cmd = ConcreteTestCommand()

        assert isinstance(cmd, Command)
        assert hasattr(cmd, 'name')
        assert hasattr(cmd, 'aliases')
        assert hasattr(cmd, 'description')
        assert hasattr(cmd, 'validate')
        assert hasattr(cmd, 'get_steps')
        assert hasattr(cmd, 'matches')

    def test_aliases_property_immutable(self):
        """Test that aliases property returns list"""
        cmd = ConcreteTestCommand(aliases=["a", "b"])
        aliases = cmd.aliases

        assert isinstance(aliases, list)
        assert aliases == ["a", "b"]

    def test_multiple_commands_different_names(self):
        """Test multiple command instances with different names"""
        cmd1 = ConcreteTestCommand(name="build")
        cmd2 = ConcreteTestCommand(name="test")

        assert cmd1.matches("build")
        assert not cmd1.matches("test")
        assert cmd2.matches("test")
        assert not cmd2.matches("build")

    def test_command_with_complex_aliases(self):
        """Test command with complex alias patterns"""
        cmd = ConcreteTestCommand(
            name="compile",
            aliases=["c", "comp", "build", "make"]
        )

        for alias in ["compile", "c", "comp", "build", "make"]:
            assert cmd.matches(alias)

        assert not cmd.matches("run")
        assert not cmd.matches("execute")


class CustomValidationCommand(Command):
    """Command with custom validation logic for testing"""

    def __init__(self, required_key: str = "required"):
        super().__init__()
        self.required_key = required_key

    @property
    def name(self) -> str:
        return "custom_validation"

    def validate(self, context: Any) -> tuple[bool, Optional[str]]:
        if not isinstance(context, dict):
            return False, "Context must be a dictionary"

        if self.required_key not in context:
            return False, f"Missing required key: {self.required_key}"

        return True, None

    def get_steps(self, context: Any) -> list[dict[str, Any]]:
        return [{"type": "custom", "value": context.get(self.required_key)}]


class TestCustomValidationCommand:
    """Test custom validation logic"""

    def test_custom_validation_success(self):
        """Test custom validation success"""
        cmd = CustomValidationCommand("test_key")
        context = {"test_key": "value"}

        is_valid, error = cmd.validate(context)

        assert is_valid
        assert error is None

    def test_custom_validation_missing_key(self):
        """Test custom validation with missing key"""
        cmd = CustomValidationCommand("required_key")
        context = {"other_key": "value"}

        is_valid, error = cmd.validate(context)

        assert not is_valid
        assert error == "Missing required key: required_key"

    def test_custom_validation_wrong_type(self):
        """Test custom validation with wrong context type"""
        cmd = CustomValidationCommand()
        context = "not a dict"

        is_valid, error = cmd.validate(context)

        assert not is_valid
        assert error == "Context must be a dictionary"

    def test_custom_get_steps(self):
        """Test custom get_steps implementation"""
        cmd = CustomValidationCommand("data")
        context = {"data": "test_value"}

        steps = cmd.get_steps(context)

        assert len(steps) == 1
        assert steps[0]["type"] == "custom"
        assert steps[0]["value"] == "test_value"
