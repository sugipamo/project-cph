import pytest
from typing import Any, Optional
from src.operations.base_command import Command


class TestCommand:
    class ConcreteCommand(Command):
        """Concrete implementation for testing"""
        def __init__(self, name: str = "test_command"):
            super().__init__()
            self._name = name
            self._aliases = ["alias1", "alias2"]
            self._description = "Test command description"
        
        @property
        def name(self) -> str:
            return self._name
        
        def validate(self, context: Any) -> tuple[bool, Optional[str]]:
            if context is None:
                return False, "Context cannot be None"
            return True, None
        
        def get_steps(self, context: Any) -> list[dict[str, Any]]:
            return [
                {"step": 1, "action": "prepare"},
                {"step": 2, "action": "execute"},
                {"step": 3, "action": "cleanup"}
            ]
    
    def test_command_is_abstract(self):
        """Test that Command is abstract and cannot be instantiated"""
        with pytest.raises(TypeError):
            Command()
    
    def test_command_initialization(self):
        """Test Command initialization through concrete class"""
        cmd = self.ConcreteCommand()
        assert isinstance(cmd._aliases, list)
        assert cmd._aliases == ["alias1", "alias2"]
        assert isinstance(cmd._description, str)
        assert cmd._description == "Test command description"
    
    def test_command_properties(self):
        """Test command properties"""
        cmd = self.ConcreteCommand()
        assert cmd.name == "test_command"
        assert cmd.aliases == ["alias1", "alias2"]
        assert cmd.description == "Test command description"
    
    def test_command_matches(self):
        """Test command matching functionality"""
        cmd = self.ConcreteCommand()
        
        # Test matching by name
        assert cmd.matches("test_command") is True
        
        # Test matching by aliases
        assert cmd.matches("alias1") is True
        assert cmd.matches("alias2") is True
        
        # Test non-matching
        assert cmd.matches("other_command") is False
        assert cmd.matches("") is False
    
    def test_command_validate(self):
        """Test command validation"""
        cmd = self.ConcreteCommand()
        
        # Valid context
        is_valid, error = cmd.validate({"key": "value"})
        assert is_valid is True
        assert error is None
        
        # Invalid context
        is_valid, error = cmd.validate(None)
        assert is_valid is False
        assert error == "Context cannot be None"
    
    def test_command_get_steps(self):
        """Test getting command steps"""
        cmd = self.ConcreteCommand()
        steps = cmd.get_steps({"context": "test"})
        
        assert len(steps) == 3
        assert steps[0] == {"step": 1, "action": "prepare"}
        assert steps[1] == {"step": 2, "action": "execute"}
        assert steps[2] == {"step": 3, "action": "cleanup"}
    
    def test_command_inheritance(self):
        """Test that ConcreteCommand inherits from Command"""
        cmd = self.ConcreteCommand()
        assert isinstance(cmd, Command)