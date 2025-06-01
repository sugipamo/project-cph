"""
Integration test for command line parsing
Tests end-to-end command line argument parsing to prevent regressions
"""
import pytest
from unittest.mock import MagicMock

from src.context.parsers.input_parser import InputParser
from src.context.execution_context import ExecutionContext
from src.context.resolver.config_resolver import create_config_root_from_dict


class TestCommandLineParsing:
    """Test command line parsing scenarios"""
    
    def setup_method(self):
        """Setup test environment"""
        # Mock config root with python and rust languages
        self.mock_config = {
            "python": {
                "aliases": ["py"],
                "commands": {
                    "open": {"aliases": ["o"], "description": "Open contest"},
                    "test": {"aliases": ["t"], "description": "Run test"},
                    "submit": {"aliases": ["s"], "description": "Submit"}
                },
                "env_types": {
                    "docker": {"aliases": ["docker"]},
                    "local": {"aliases": ["local"]}
                }
            },
            "rust": {
                "aliases": ["rs"],
                "commands": {
                    "open": {"aliases": ["o"], "description": "Open contest"},
                    "test": {"aliases": ["t"], "description": "Run test"}
                },
                "env_types": {
                    "docker": {"aliases": ["docker"]},
                    "local": {"aliases": ["local"]}
                }
            }
        }
        self.root = create_config_root_from_dict(self.mock_config)
    
    def create_context(self, **kwargs):
        """Create test context with defaults"""
        defaults = {
            "command_type": "test",
            "language": "python", 
            "contest_name": "abc300",
            "problem_name": "a",
            "env_type": "docker",
            "env_json": None,
            "resolver": None
        }
        defaults.update(kwargs)
        return MagicMock(spec=ExecutionContext, **defaults)
    
    def test_language_parsing_regression_open_command(self):
        """
        Regression test: ensure 'open' command is not mistaken for language
        Critical fix: commands should not be parsed as languages
        """
        # Setup context with python as default language
        context = self.create_context(language="python")
        
        # Parse arguments: abc300 open a
        args = ["abc300", "open", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        # Critical assertions
        assert parsed_context.language == "python", f"Language incorrectly changed to: {parsed_context.language}"
        assert parsed_context.command_type == "open", f"Command not correctly parsed: {parsed_context.command_type}"
        assert parsed_context.contest_name == "abc300"
        assert parsed_context.problem_name == "a"
        assert len(remaining_args) == 0, f"Unexpected remaining args: {remaining_args}"
    
    def test_language_parsing_with_explicit_language(self):
        """Test that explicit language specification works correctly"""
        context = self.create_context(language="python")
        
        # Parse arguments: py abc300 open a
        args = ["py", "abc300", "open", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        assert parsed_context.language == "python"  # py -> python
        assert parsed_context.command_type == "open"
        assert parsed_context.contest_name == "abc300"
        assert parsed_context.problem_name == "a"
        assert len(remaining_args) == 0
    
    def test_language_parsing_rust_language(self):
        """Test rust language specification"""
        context = self.create_context(language="python")
        
        # Parse arguments: rust abc300 test a
        args = ["rust", "abc300", "test", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        assert parsed_context.language == "rust"
        assert parsed_context.command_type == "test"
        assert parsed_context.contest_name == "abc300"
        assert parsed_context.problem_name == "a"
        assert len(remaining_args) == 0
    
    def test_command_aliases(self):
        """Test that command aliases work correctly"""
        context = self.create_context(language="python")
        
        # Parse arguments: abc300 o a (o is alias for open)
        args = ["abc300", "o", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        assert parsed_context.language == "python"
        assert parsed_context.command_type == "open"  # o -> open
        assert parsed_context.contest_name == "abc300"
        assert parsed_context.problem_name == "a"
        assert len(remaining_args) == 0
    
    def test_parsing_order_independence(self):
        """Test different command variations maintain language integrity"""
        test_cases = [
            (["abc300", "open", "a"], "open"),
            (["abc300", "test", "a"], "test"),
            (["abc300", "submit", "a"], "submit"),
            (["abc300", "o", "a"], "open"),  # alias
            (["abc300", "t", "a"], "test"),  # alias
            (["abc300", "s", "a"], "submit"),  # alias
        ]
        
        for args, expected_command in test_cases:
            context = self.create_context(language="python")
            remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
            
            assert parsed_context.language == "python", f"Language changed for args {args}"
            assert parsed_context.command_type == expected_command, f"Command not parsed correctly for args {args}"
            assert parsed_context.contest_name == "abc300"
            assert parsed_context.problem_name == "a"
    
    def test_edge_case_language_like_commands(self):
        """Test commands that could be confused with languages don't affect language parsing"""
        # Add a command that looks like a language
        config_with_edge_case = dict(self.mock_config)
        config_with_edge_case["python"]["commands"]["rust"] = {"description": "Special rust command"}
        root = create_config_root_from_dict(config_with_edge_case)
        
        context = self.create_context(language="python")
        
        # Parse arguments: abc300 rust a (rust as command, not language)
        args = ["abc300", "rust", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, root)
        
        # Language should remain python (not changed to rust)
        assert parsed_context.language == "python", "Language incorrectly changed by command name"
        assert parsed_context.command_type == "rust"
        assert parsed_context.contest_name == "abc300"
        assert parsed_context.problem_name == "a"
    
    def test_minimal_arguments(self):
        """Test parsing with minimal arguments"""
        context = self.create_context(language="python")
        
        # Just contest name
        args = ["abc123"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        assert parsed_context.contest_name == "abc123"
        assert parsed_context.language == "python"  # Should remain unchanged
        # Other values should remain from original context
        assert parsed_context.command_type == "test"  # From original context
        assert len(remaining_args) == 0
    
    def test_language_only_checks_first_level_nodes(self):
        """
        Test that language parsing only checks first-level nodes,
        not deep nested command nodes
        """
        context = self.create_context(language="python")
        
        # This should NOT find "open" as a language, even though it exists
        # in python.commands.open
        args = ["open", "abc300", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        # "open" should not be recognized as a language
        # It should remain in args and be processed as a command later
        assert parsed_context.language == "python"  # Should not change
        assert parsed_context.command_type == "open"  # Should be parsed as command
        assert parsed_context.contest_name == "abc300"
        assert parsed_context.problem_name == "a"