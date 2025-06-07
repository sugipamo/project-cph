"""
Output utilities for consistent logging and display across the application.

This module provides utilities to standardize output formatting and display
throughout the application, complementing the OutputManager for business logic output.
"""
from typing import Any, Optional
from enum import Enum


class OutputLevel(Enum):
    """Output levels for different types of messages."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    SUCCESS = "SUCCESS"
    WARNING = "WARNING"
    ERROR = "ERROR"


class OutputFormatter:
    """Formatter for consistent output display."""
    
    @staticmethod
    def format_task_result(task_name: str, success: bool, details: str = None) -> str:
        """
        Format task execution result consistently.
        
        Args:
            task_name: Name of the task
            success: Whether the task succeeded
            details: Optional details about the result
            
        Returns:
            Formatted string for display
        """
        symbol = "✓" if success else "✗"
        status = "成功" if success else "失敗"
        result = f"  {symbol} {task_name}: {status}"
        
        if details:
            result += f" - {details}"
        
        return result
    
    @staticmethod
    def format_step_summary(step_num: int, total_steps: int, status: str) -> str:
        """
        Format step summary consistently.
        
        Args:
            step_num: Current step number
            total_steps: Total number of steps
            status: Status string
            
        Returns:
            Formatted step summary
        """
        return f"\nステップ {step_num}/{total_steps}: {status}"
    
    @staticmethod
    def format_completion_summary(successful: int, total: int, task_type: str = "ステップ") -> str:
        """
        Format completion summary consistently.
        
        Args:
            successful: Number of successful items
            total: Total number of items
            task_type: Type of task (ステップ, タスク, etc.)
            
        Returns:
            Formatted completion summary
        """
        return f"\n実行完了: {successful}/{total} {task_type}成功"
    
    @staticmethod
    def format_section_header(title: str) -> str:
        """
        Format section header consistently.
        
        Args:
            title: Section title
            
        Returns:
            Formatted section header
        """
        return f"\n=== {title} ==="


class OutputUtils:
    """Utilities for consistent output across the application."""
    
    def __init__(self, enable_debug: bool = False):
        self.enable_debug = enable_debug
        self.formatter = OutputFormatter()
    
    def print_message(self, message: str, level: OutputLevel = OutputLevel.INFO, 
                     end: str = "\n") -> None:
        """
        Print message with optional level indication.
        
        Args:
            message: Message to print
            level: Output level
            end: String appended after the message
        """
        if level == OutputLevel.DEBUG and not self.enable_debug:
            return
        
        # Add level prefix for warnings and errors
        if level == OutputLevel.WARNING:
            message = f"警告: {message}"
        elif level == OutputLevel.ERROR:
            message = f"エラー: {message}"
        
        print(message, end=end)
    
    def print_task_result(self, task_name: str, success: bool, details: str = None) -> None:
        """Print formatted task result."""
        formatted = self.formatter.format_task_result(task_name, success, details)
        self.print_message(formatted)
    
    def print_step_summary(self, step_num: int, total_steps: int, status: str) -> None:
        """Print formatted step summary."""
        formatted = self.formatter.format_step_summary(step_num, total_steps, status)
        self.print_message(formatted)
    
    def print_completion_summary(self, successful: int, total: int, task_type: str = "ステップ") -> None:
        """Print formatted completion summary."""
        formatted = self.formatter.format_completion_summary(successful, total, task_type)
        self.print_message(formatted)
    
    def print_section_header(self, title: str) -> None:
        """Print formatted section header."""
        formatted = self.formatter.format_section_header(title)
        self.print_message(formatted)
    
    def print_warning(self, message: str) -> None:
        """Print warning message."""
        self.print_message(message, OutputLevel.WARNING)
    
    def print_error(self, message: str) -> None:
        """Print error message."""
        self.print_message(message, OutputLevel.ERROR)
    
    def print_success(self, message: str) -> None:
        """Print success message."""
        self.print_message(message, OutputLevel.SUCCESS)
    
    def print_debug(self, message: str) -> None:
        """Print debug message (only if debug enabled)."""
        self.print_message(message, OutputLevel.DEBUG)


# Global instance for convenience
_output_utils = OutputUtils()


def get_output_utils(enable_debug: bool = False) -> OutputUtils:
    """Get output utils instance."""
    if enable_debug != _output_utils.enable_debug:
        _output_utils.enable_debug = enable_debug
    return _output_utils


# Convenience functions
def print_task_result(task_name: str, success: bool, details: str = None) -> None:
    """Print formatted task result."""
    _output_utils.print_task_result(task_name, success, details)


def print_step_summary(step_num: int, total_steps: int, status: str) -> None:
    """Print formatted step summary."""
    _output_utils.print_step_summary(step_num, total_steps, status)


def print_completion_summary(successful: int, total: int, task_type: str = "ステップ") -> None:
    """Print formatted completion summary."""
    _output_utils.print_completion_summary(successful, total, task_type)


def print_section_header(title: str) -> None:
    """Print formatted section header."""
    _output_utils.print_section_header(title)


def print_warning(message: str) -> None:
    """Print warning message."""
    _output_utils.print_warning(message)


def print_error(message: str) -> None:
    """Print error message."""
    _output_utils.print_error(message)


def print_success(message: str) -> None:
    """Print success message."""
    _output_utils.print_success(message)