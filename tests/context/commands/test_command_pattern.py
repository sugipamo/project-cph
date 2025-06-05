"""
Test Command pattern implementation
"""
import pytest
from src.context.commands.base_command import Command
from src.context.commands.concrete_commands import OpenCommand, TestRunCommand, SubmitCommand
from src.context.commands.command_registry import get_command, get_all_commands, CommandRegistry


class TestCommandPattern:
    
    def test_open_command(self):
        """Test OpenCommand implementation"""
        cmd = OpenCommand()
        assert cmd.name == "open"
        assert "o" in cmd.aliases
        assert cmd.description == "コンテストを開く"
        
        # Test matching
        assert cmd.matches("open")
        assert cmd.matches("o")
        assert not cmd.matches("test")
    
    def test_test_command(self):
        """Test TestRunCommand implementation"""
        cmd = TestRunCommand()
        assert cmd.name == "test"
        assert "t" in cmd.aliases
        assert cmd.description == "テストを実行する"
        
        # Test matching
        assert cmd.matches("test")
        assert cmd.matches("t")
        assert not cmd.matches("open")
    
    def test_submit_command(self):
        """Test SubmitCommand implementation"""
        cmd = SubmitCommand()
        assert cmd.name == "submit"
        assert "s" in cmd.aliases
        assert cmd.description == "提出する"
        
        # Test matching
        assert cmd.matches("submit")
        assert cmd.matches("s")
        assert not cmd.matches("test")
    
    def test_command_registry(self):
        """Test CommandRegistry functionality"""
        registry = CommandRegistry()
        
        # Test getting command by name
        cmd = registry.get_command("open")
        assert cmd is not None
        assert isinstance(cmd, OpenCommand)
        
        # Test getting command by alias
        cmd = registry.get_command("o")
        assert cmd is not None
        assert isinstance(cmd, OpenCommand)
        
        # Test getting non-existent command
        cmd = registry.get_command("nonexistent")
        assert cmd is None
        
        # Test getting all commands
        all_commands = registry.get_all_commands()
        assert len(all_commands) >= 4  # At least open, test, submit, new
        
        # Test command names include aliases
        names = registry.get_command_names()
        assert "open" in names
        assert "o" in names
        assert "test" in names
        assert "t" in names
    
    def test_global_registry_functions(self):
        """Test global registry functions"""
        # Test get_command
        cmd = get_command("open")
        assert cmd is not None
        assert isinstance(cmd, OpenCommand)
        
        # Test get_all_commands
        all_commands = get_all_commands()
        assert len(all_commands) >= 4
    
    def test_command_validation(self):
        """Test command validation logic"""
        # Create a mock context
        class MockContext:
            def __init__(self):
                self.contest_name = None
                self.problem_name = None
        
        context = MockContext()
        cmd = OpenCommand()
        
        # Test validation failure
        is_valid, error = cmd.validate(context)
        assert not is_valid
        assert "Contest name is required" in error
        
        # Test partial validation failure
        context.contest_name = "abc300"
        is_valid, error = cmd.validate(context)
        assert not is_valid
        assert "Problem name is required" in error
        
        # Test validation success
        context.problem_name = "a"
        is_valid, error = cmd.validate(context)
        assert is_valid
        assert error is None