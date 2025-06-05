"""
Base command class for the command pattern implementation
"""
from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional


class Command(ABC):
    """
    Abstract base class for all commands.
    Encapsulates command behavior and validation.
    """
    
    def __init__(self):
        self._aliases: List[str] = []
        self._description: str = ""
    
    @property
    @abstractmethod
    def name(self) -> str:
        """The primary name of the command"""
        pass
    
    @property
    def aliases(self) -> List[str]:
        """Alternative names for the command"""
        return self._aliases
    
    @property
    def description(self) -> str:
        """Human-readable description of the command"""
        return self._description
    
    @abstractmethod
    def validate(self, context: Any) -> tuple[bool, Optional[str]]:
        """
        Validate if the command can be executed in the given context.
        
        Returns:
            tuple[bool, Optional[str]]: (is_valid, error_message)
        """
        pass
    
    @abstractmethod
    def get_steps(self, context: Any) -> List[Dict[str, Any]]:
        """
        Get the execution steps for this command.
        
        Returns:
            List of step dictionaries
        """
        pass
    
    def matches(self, command_str: str) -> bool:
        """
        Check if the given string matches this command.
        
        Args:
            command_str: The command string to check
            
        Returns:
            True if the string matches this command or its aliases
        """
        if command_str == self.name:
            return True
        return command_str in self.aliases