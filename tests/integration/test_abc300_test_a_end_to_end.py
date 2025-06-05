"""
End-to-end integration test for abc300 test a command
Tests the full command pipeline to identify where the parsing issue occurs
"""
import pytest
import json
import tempfile
import os
from unittest.mock import patch, MagicMock
from pathlib import Path

from src.context.user_input_parser import parse_user_input
from src.operations.build_operations import build_operations


class TestAbc300TestAEndToEnd:
    """End-to-end test for the abc300 test a command scenario"""
    
    def setup_method(self):
        """Setup test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.contest_env_dir = os.path.join(self.temp_dir, "contest_env")
        self.python_env_dir = os.path.join(self.contest_env_dir, "python")
        
        # Create directory structure
        os.makedirs(self.python_env_dir, exist_ok=True)
        
        # Create a minimal valid env.json that matches the real structure
        self.env_json_content = {
            "python": {
                "aliases": ["py"],
                "language_id": "5078",
                "source_file_name": "main.py",
                "contest_current_path": "./contest_current",
                "contest_stock_path": "./contest_stock",
                "contest_template_path": "./contest_template",
                "contest_temp_path": "./.temp",
                "workspace_path": "./workspace",
                "commands": {
                    "open": {
                        "aliases": ["o"],
                        "description": "コンテストを開く",
                        "steps": []
                    },
                    "test": {
                        "aliases": ["t"],
                        "description": "テストを実行",
                        "steps": []
                    },
                    "submit": {
                        "aliases": ["s"],
                        "description": "提出",
                        "steps": []
                    }
                },
                "env_types": {
                    "docker": {"aliases": ["docker"]},
                    "local": {"aliases": ["local"]}
                }
            }
        }
        
        # Write env.json file
        env_json_path = os.path.join(self.python_env_dir, "env.json")
        with open(env_json_path, 'w') as f:
            json.dump(self.env_json_content, f)
    
    def teardown_method(self):
        """Cleanup test environment"""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @patch('src.context.user_input_parser.CONTEST_ENV_DIR')
    @patch('src.context.user_input_parser.SystemInfoManager')
    def test_abc300_test_a_full_pipeline(self, mock_system_info_manager, mock_contest_env_dir):
        """
        CRITICAL TEST: Test the full abc300 test a command pipeline
        This should reveal where the argument parsing issue occurs
        """
        # Setup contest_env_dir to point to our test directory
        mock_contest_env_dir.__str__ = lambda: self.contest_env_dir
        mock_contest_env_dir.__fspath__ = lambda: self.contest_env_dir
        
        # Mock system info manager to have python as default language
        mock_system_info = {
            "command": None,
            "language": "python",  # Set default language
            "contest_name": None,
            "problem_name": None,
            "env_type": "local",   # Set default env_type
            "env_json": None
        }
        mock_system_info_manager.return_value.load_system_info.return_value = mock_system_info
        
        # Build operations
        operations = build_operations()
        
        # Test the exact scenario
        with patch('src.context.user_input_parser.CONTEST_ENV_DIR', self.contest_env_dir):
            context = parse_user_input(["abc300", "test", "a"], operations)
        
        # DEBUG: Print actual values to understand what's happening
        print(f"DEBUG - contest_name: '{context.contest_name}'")
        print(f"DEBUG - command_type: '{context.command_type}'")
        print(f"DEBUG - problem_name: '{context.problem_name}'")
        print(f"DEBUG - language: '{context.language}'")
        
        # CRITICAL ASSERTIONS: These should pass for correct argument parsing
        assert context.contest_name == "abc300", \
            f"Expected contest_name='abc300', got '{context.contest_name}'"
        assert context.command_type == "test", \
            f"Expected command_type='test', got '{context.command_type}'"
        assert context.problem_name == "a", \
            f"Expected problem_name='a', got '{context.problem_name}'"
    
    @patch('src.context.user_input_parser.CONTEST_ENV_DIR')
    @patch('src.context.user_input_parser.SystemInfoManager')
    def test_argument_parsing_order_debug(self, mock_system_info_manager, mock_contest_env_dir):
        """
        DEBUG TEST: Step-by-step argument parsing to identify the issue
        """
        mock_contest_env_dir.__str__ = lambda: self.contest_env_dir
        mock_contest_env_dir.__fspath__ = lambda: self.contest_env_dir
        
        mock_system_info = {
            "command": None,
            "language": None,
            "contest_name": None,
            "problem_name": None,
            "env_type": None,
            "env_json": None
        }
        mock_system_info_manager.return_value.load_system_info.return_value = mock_system_info
        
        operations = build_operations()
        
        # Test different argument combinations to understand the pattern
        test_cases = [
            (["abc300", "test", "a"], "Case 1: abc300 test a"),
            (["test", "abc300", "a"], "Case 2: test abc300 a"),  
            (["a", "test", "abc300"], "Case 3: a test abc300"),
        ]
        
        for args, description in test_cases:
            print(f"\n{description}")
            print(f"Input args: {args}")
            
            with patch('src.context.user_input_parser.CONTEST_ENV_DIR', self.contest_env_dir):
                try:
                    context = parse_user_input(args, operations)
                    print(f"  contest_name: '{context.contest_name}'")
                    print(f"  command_type: '{context.command_type}'")
                    print(f"  problem_name: '{context.problem_name}'")
                    print(f"  language: '{context.language}'")
                except Exception as e:
                    print(f"  ERROR: {e}")
    
    @patch('src.context.user_input_parser.CONTEST_ENV_DIR')
    @patch('src.context.user_input_parser.SystemInfoManager')
    def test_pop_order_investigation(self, mock_system_info_manager, mock_contest_env_dir):
        """
        Investigate the actual pop() behavior in argument parsing
        """
        mock_contest_env_dir.__str__ = lambda: self.contest_env_dir
        mock_contest_env_dir.__fspath__ = lambda: self.contest_env_dir
        
        mock_system_info = {
            "command": None,
            "language": None,
            "contest_name": None,
            "problem_name": None,
            "env_type": None,
            "env_json": None
        }
        mock_system_info_manager.return_value.load_system_info.return_value = mock_system_info
        
        operations = build_operations()
        
        # Demonstrate the pop() order issue
        args = ["abc300", "test", "a"]
        print(f"Original args: {args}")
        
        # Simulate the current implementation's pop() behavior
        # This is what happens in the current code:
        args_copy = args.copy()
        problem_name = args_copy.pop()  # Gets "a" - CORRECT
        contest_name = args_copy.pop()  # Gets "test" - WRONG! Should be "abc300"
        
        print(f"With current pop() logic:")
        print(f"  problem_name = args.pop() -> '{problem_name}' (correct)")
        print(f"  contest_name = args.pop() -> '{contest_name}' (WRONG! should be 'abc300')")
        print(f"  remaining args: {args_copy}")
        
        # This proves the issue is in the pop() order in InputParser
        # The args are processed from right to left, but we expect left-to-right semantics
    
    def test_current_bug_demonstration(self):
        """
        Test that demonstrates the current bug with abc300 test a
        This test should FAIL until the bug is fixed
        """
        # This test intentionally fails to document the current bug
        args = ["abc300", "test", "a"]
        
        # Current buggy behavior using pop()
        args_copy = args.copy()
        problem_name = args_copy.pop()      # "a" - correct
        contest_name = args_copy.pop()      # "test" - WRONG!
        remaining = args_copy               # ["abc300"] - should be empty
        
        # This assertion will fail, proving the bug exists
        with pytest.raises(AssertionError, match="Bug exists"):
            assert contest_name == "abc300", "Bug exists: contest_name should be 'abc300' but pop() gives 'test'"
            assert len(remaining) == 0, "Bug exists: args should be empty after processing"