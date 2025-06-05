"""
Command registry for managing available commands
"""
from typing import Dict, List, Optional
from .base_command import Command
from .concrete_commands import OpenCommand, TestRunCommand, SubmitCommand, NewCommand


class CommandRegistry:
    """
    Registry for all available commands.
    Provides command lookup and management.
    """
    
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._initialize_default_commands()
    
    def _initialize_default_commands(self):
        """Initialize with default commands"""
        default_commands = [
            OpenCommand(),
            TestRunCommand(),
            SubmitCommand(),
            NewCommand(),
        ]
        
        for command in default_commands:
            self.register(command)
    
    def register(self, command: Command):
        """
        Register a command in the registry.
        
        Args:
            command: The command to register
        """
        # Register by primary name
        self._commands[command.name] = command
        
        # Register by aliases
        for alias in command.aliases:
            self._commands[alias] = command
    
    def get_command(self, command_str: str) -> Optional[Command]:
        """
        Get a command by name or alias.
        
        Args:
            command_str: The command string to look up
            
        Returns:
            The command if found, None otherwise
        """
        return self._commands.get(command_str)
    
    def get_all_commands(self) -> List[Command]:
        """
        Get all unique commands (not including aliases).
        
        Returns:
            List of all registered commands
        """
        # Use dict to remove duplicates (commands registered under multiple names)
        unique_commands = {}
        for command in self._commands.values():
            unique_commands[command.name] = command
        return list(unique_commands.values())
    
    def get_command_names(self) -> List[str]:
        """
        Get all command names including aliases.
        
        Returns:
            List of all command names and aliases
        """
        return list(self._commands.keys())


# Global registry instance
_registry = CommandRegistry()


def get_command(command_str: str) -> Optional[Command]:
    """Get a command from the global registry"""
    return _registry.get_command(command_str)


def get_all_commands() -> List[Command]:
    """Get all commands from the global registry"""
    return _registry.get_all_commands()


def register_command(command: Command):
    """Register a command in the global registry"""
    _registry.register(command)