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
    
    def test_abc300_test_a_scenario_specific(self):
        """
        REGRESSION TEST: Test the specific abc300 test a scenario that's failing
        This addresses the bug where arguments are parsed in wrong order
        """
        context = self.create_context(language="python")
        
        # The exact scenario: abc300 test a
        args = ["abc300", "test", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        # CRITICAL: Verify correct parsing order
        assert parsed_context.contest_name == "abc300", f"Expected contest_name='abc300', got '{parsed_context.contest_name}'"
        assert parsed_context.command_type == "test", f"Expected command_type='test', got '{parsed_context.command_type}'"
        assert parsed_context.problem_name == "a", f"Expected problem_name='a', got '{parsed_context.problem_name}'"
        assert parsed_context.language == "python"  # Should remain unchanged
        assert len(remaining_args) == 0, f"Expected no remaining args, got {remaining_args}"
    
    def test_abc300_test_a_with_aliases(self):
        """Test abc300 test a scenario with command aliases"""
        context = self.create_context(language="python")
        
        # Using alias 't' instead of 'test'
        args = ["abc300", "t", "a"]
        remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
        
        assert parsed_context.contest_name == "abc300"
        assert parsed_context.command_type == "test"  # t -> test
        assert parsed_context.problem_name == "a"
        assert parsed_context.language == "python"
        assert len(remaining_args) == 0
    
    def test_abc300_test_a_various_contest_formats(self):
        """Test various contest name formats with test a"""
        context = self.create_context(language="python")
        
        contest_patterns = [
            "abc300", "abc301", "arc100", "agc050", 
            "typical90", "dp", "math", "graph"
        ]
        
        for contest in contest_patterns:
            args = [contest, "test", "a"]
            remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
            
            assert parsed_context.contest_name == contest, f"Contest parsing failed for {contest}"
            assert parsed_context.command_type == "test"
            assert parsed_context.problem_name == "a"
            assert len(remaining_args) == 0
    
    def test_abc300_test_various_problems(self):
        """Test abc300 test with various problem names"""
        context = self.create_context(language="python")
        
        problem_names = ["a", "b", "c", "d", "e", "f", "ex"]
        
        for problem in problem_names:
            args = ["abc300", "test", problem]
            remaining_args, parsed_context = InputParser.parse_command_line(args, context, self.root)
            
            assert parsed_context.contest_name == "abc300"
            assert parsed_context.command_type == "test"
            assert parsed_context.problem_name == problem, f"Problem parsing failed for {problem}"
            assert len(remaining_args) == 0
    
    def test_argument_order_parsing_regression(self):
        """
        CRITICAL REGRESSION TEST: Ensure arguments are processed in correct order
        This tests the core issue with the abc300 test a command
        """
        context = self.create_context(language="python")
        
        # Test different argument orders that should all work
        test_cases = [
            # (args, expected_contest, expected_command, expected_problem)
            (["abc300", "test", "a"], "abc300", "test", "a"),
            (["contest123", "open", "b"], "contest123", "open", "b"),
            (["xyz", "submit", "c"], "xyz", "submit", "c"),
            (["typical90", "t", "001"], "typical90", "test", "001"),  # with alias
        ]
        
        for args, exp_contest, exp_command, exp_problem in test_cases:
            context_copy = self.create_context(language="python")
            remaining_args, parsed_context = InputParser.parse_command_line(args, context_copy, self.root)
            
            assert parsed_context.contest_name == exp_contest, \
                f"Args {args}: expected contest '{exp_contest}', got '{parsed_context.contest_name}'"
            assert parsed_context.command_type == exp_command, \
                f"Args {args}: expected command '{exp_command}', got '{parsed_context.command_type}'"
            assert parsed_context.problem_name == exp_problem, \
                f"Args {args}: expected problem '{exp_problem}', got '{parsed_context.problem_name}'"
            assert len(remaining_args) == 0, \
                f"Args {args}: unexpected remaining arguments {remaining_args}"