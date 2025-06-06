"""
E2E tests for src/main.py using mock drivers through DI container
Tests the actual main() function with real workflow execution but mock I/O operations
"""
import pytest
import json
import tempfile
import os
from pathlib import Path
from io import StringIO
import sys

from src.main import main
from src.operations.build_operations import build_mock_operations
from src.context.user_input_parser import parse_user_input
from src.workflow_execution_service import WorkflowExecutionResult


class TestMainE2EMock:
    """E2E tests for main() function using mock drivers"""
    
    def setup_method(self):
        """Setup test fixtures with mock operations"""
        self.operations = build_mock_operations()
        self.mock_file_driver = self.operations.resolve('file_driver')
        self.mock_shell_driver = self.operations.resolve('shell_driver')
        self.mock_docker_driver = self.operations.resolve('docker_driver')
        self.mock_python_driver = self.operations.resolve('python_driver')
        
        # Clear any previous state
        self.mock_file_driver.files.clear()
        self.mock_file_driver.contents.clear()
        self.mock_file_driver.operations.clear()
        self.mock_shell_driver.calls.clear()
        self.mock_shell_driver.expected_results.clear()
        self.mock_python_driver.reset()
        
        # Create directory structure in mock filesystem
        self.mock_file_driver.files.add(self.mock_file_driver.base_dir / Path("contest_env"))
        self.mock_file_driver.files.add(self.mock_file_driver.base_dir / Path("contest_env/python"))
        
        # Set default mock behavior for Python commands
        self.mock_python_driver.set_default_result(
            stdout="Mock python execution",
            stderr="",
            returncode=0
        )
        
        # Mock webbrowser.open to prevent actual browser opening
        self.mock_python_driver.set_expected_result(
            "webbrowser.open",
            stdout="Mock browser opened",
            stderr="",
            returncode=0
        )
    
    def test_main_successful_python_execution(self):
        """Test successful Python script execution workflow"""
        # Setup mock filesystem with contest directory and Python script
        self.mock_file_driver._create_impl(
            "contest_stock/abc300/a/main.py",
            'print("Hello AtCoder")\n'
        )
        
        # Setup required file for test command (contest_current/main.py)
        self.mock_file_driver._create_impl(
            "contest_current/main.py",
            'print("Current contest file")\n'
        )
        
        # Setup system_info.json
        system_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc300",
            "problem_name": "a"
        }
        self.mock_file_driver._create_impl(
            "system_info.json",
            json.dumps(system_info, ensure_ascii=False, indent=2)
        )
        
        # Setup env.json for Python
        env_config = {
            "python": {
                "aliases": ["py"],
                "commands": {
                    "test": {
                        "aliases": ["t"],
                        "steps": [
                            {"type": "shell", "cmd": ["python", "contest_stock/abc300/a/main.py"]}
                        ]
                    }
                },
                "env_types": {
                    "local": {
                        "aliases": ["local"]
                    }
                }
            }
        }
        self.mock_file_driver._create_impl(
            "contest_env/python/env.json",
            json.dumps(env_config, ensure_ascii=False, indent=2)
        )
        
        # Mock shell execution to simulate successful Python script run
        # The command is passed as a list, so we need to match the string representation
        self.mock_shell_driver.set_expected_result(
            "python", # substring match for "python" command
            stdout="Hello AtCoder\n",
            stderr="",
            returncode=0
        )
        
        # Parse arguments and create context
        # Since system_info.json already contains the required information,
        # we might not need all arguments, but let's try with empty args first
        args = []
        context = parse_user_input(args, self.operations)
        
        # Execute main function
        result = main(context, self.operations)
        
        # Verify successful execution
        assert isinstance(result, WorkflowExecutionResult)
        assert result.success is True
        assert len(result.results) > 0
    
    def test_main_file_not_found_error(self):
        """Test main() behavior when Python script file doesn't exist"""
        # Setup system_info.json with non-existent script
        system_info = {
            "command": "test",
            "language": "python",
            "env_type": "local", 
            "contest_name": "abc999",
            "problem_name": "z"
        }
        self.mock_file_driver._create_impl(
            "system_info.json",
            json.dumps(system_info, ensure_ascii=False, indent=2)
        )
        
        # Setup env.json
        env_config = {
            "python": {
                "aliases": ["py"],
                "commands": {
                    "test": {
                        "aliases": ["t"],
                        "steps": [
                            {"type": "shell", "cmd": ["python", "contest_stock/abc999/z/main.py"]}
                        ]
                    }
                },
                "env_types": {
                    "local": {
                        "aliases": ["local"]
                    }
                }
            }
        }
        self.mock_file_driver._create_impl(
            "contest_env/python/env.json",
            json.dumps(env_config, ensure_ascii=False, indent=2)
        )
        
        # Mock shell execution to simulate file not found
        self.mock_shell_driver.set_expected_result(
            "python contest_stock/abc999/z/main.py",
            stdout="",
            stderr="python: can't open file 'contest_stock/abc999/z/main.py': [Errno 2] No such file or directory",
            returncode=2
        )
        
        # Parse arguments and create context
        args = []
        context = parse_user_input(args, self.operations)
        
        # Capture stdout for verification
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            # Execute main function - should raise exception due to failed step
            with pytest.raises(Exception, match="ワークフロー実行に失敗しました"):
                main(context, self.operations)
                
            # Verify error output
            output = captured_output.getvalue()
            assert "エラー:" in output or "失敗" in output
            
        finally:
            sys.stdout = old_stdout
    
    def test_main_with_file_operations(self):
        """Test main() with file creation and execution workflow"""
        # Setup system_info.json
        system_info = {
            "command": "open",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc301",
            "problem_name": "b"
        }
        self.mock_file_driver._create_impl(
            "system_info.json", 
            json.dumps(system_info, ensure_ascii=False, indent=2)
        )
        
        # Setup env.json with file operations
        env_config = {
            "python": {
                "aliases": ["py"],
                "commands": {
                    "open": {
                        "aliases": ["o"],
                        "steps": [
                            {
                                "type": "file",
                                "op": "ENSURE_EXISTS",
                                "path": "contest_stock/abc301/b/main.py",
                                "template_path": "contest_template/python/main.py"
                            },
                            {
                                "type": "shell",
                                "cmd": ["python", "contest_stock/abc301/b/main.py"]
                            }
                        ]
                    }
                },
                "env_types": {
                    "local": {
                        "aliases": ["local"]
                    }
                }
            }
        }
        self.mock_file_driver._create_impl(
            "contest_env/python/env.json",
            json.dumps(env_config, ensure_ascii=False, indent=2)
        )
        
        # Setup template file
        template_content = '# Python template\nprint("Template executed")\n'
        self.mock_file_driver._create_impl(
            "contest_template/python/main.py",
            template_content
        )
        
        # Mock shell execution
        self.mock_shell_driver.set_expected_result(
            "python contest_stock/abc301/b/main.py",
            stdout="Template executed\n",
            stderr="",
            returncode=0
        )
        
        # Parse arguments and create context
        args = []
        context = parse_user_input(args, self.operations)
        
        # Capture stdout
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            # Execute main function
            result = main(context, self.operations)
            
            # Verify successful execution
            assert result.success is True
            assert len(result.results) >= 2  # File operation + shell execution
            
            # Verify file was created in mock filesystem
            assert self.mock_file_driver._exists_impl("contest_stock/abc301/b/main.py")
            file_path = self.mock_file_driver.base_dir / Path("contest_stock/abc301/b/main.py")
            created_content = self.mock_file_driver.contents.get(file_path, "")
            assert template_content == created_content
            
            # Verify output
            output = captured_output.getvalue()
            assert "ワークフロー実行完了" in output
            
        finally:
            sys.stdout = old_stdout
    
    def test_main_step_execution_details_output(self):
        """Test that main() outputs detailed step execution information"""
        # Setup simple test case
        system_info = {
            "command": "test",
            "language": "python", 
            "env_type": "local",
            "contest_name": "abc300",
            "problem_name": "a"
        }
        self.mock_file_driver._create_impl(
            "system_info.json",
            json.dumps(system_info, ensure_ascii=False, indent=2)
        )
        
        env_config = {
            "test": {
                "python": {
                    "commands": [
                        {"type": "shell", "cmd": ["echo", "test_output"]}
                    ]
                }
            }
        }
        self.mock_file_driver._create_impl(
            "contest_env/python/env.json",
            json.dumps(env_config, ensure_ascii=False, indent=2)
        )
        
        # Mock shell execution
        self.mock_shell_driver.set_expected_result(
            "echo test_output",
            stdout="test_output\n",
            stderr="",
            returncode=0
        )
        
        # Parse and execute
        args = []
        context = parse_user_input(args, self.operations)
        
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            result = main(context, self.operations)
            
            output = captured_output.getvalue()
            
            # Verify detailed step information is displayed
            assert "=== ステップ実行詳細 ===" in output
            assert "ステップ 1:" in output
            assert "✓ 成功" in output
            assert "タイプ:" in output
            assert "コマンド:" in output
            assert "標準出力:" in output
            assert "test_output" in output
            assert "終了コード: 0" in output
            assert "=== 実行完了 ===" in output
            
        finally:
            sys.stdout = old_stdout
    
    def test_main_with_multiple_step_workflow(self):
        """Test main() with multiple step workflow execution"""
        # Setup system_info.json
        system_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc300",
            "problem_name": "c"
        }
        self.mock_file_driver._create_impl(
            "system_info.json",
            json.dumps(system_info, ensure_ascii=False, indent=2)
        )
        
        # Setup env.json with multiple commands
        env_config = {
            "test": {
                "python": {
                    "commands": [
                        {"type": "shell", "cmd": ["echo", "Step 1"]},
                        {"type": "shell", "cmd": ["echo", "Step 2"]},
                        {"type": "shell", "cmd": ["echo", "Step 3"]}
                    ]
                }
            }
        }
        self.mock_file_driver._create_impl(
            "contest_env/python/env.json",
            json.dumps(env_config, ensure_ascii=False, indent=2)
        )
        
        # Mock all shell executions
        self.mock_shell_driver.set_expected_result(
            "echo Step 1",
            stdout="Step 1\n",
            stderr="",
            returncode=0
        )
        self.mock_shell_driver.set_expected_result(
            "echo Step 2",
            stdout="Step 2\n", 
            stderr="",
            returncode=0
        )
        self.mock_shell_driver.set_expected_result(
            "echo Step 3",
            stdout="Step 3\n",
            stderr="",
            returncode=0
        )
        
        # Parse and execute
        args = []
        context = parse_user_input(args, self.operations)
        
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            result = main(context, self.operations)
            
            # Verify all steps executed successfully
            assert result.success is True
            assert len(result.results) == 3
            
            output = captured_output.getvalue()
            
            # Verify completion message shows correct counts
            assert "ワークフロー実行完了: 3/3 ステップ成功" in output
            
            # Verify all steps are displayed
            assert "ステップ 1: ✓ 成功" in output
            assert "ステップ 2: ✓ 成功" in output
            assert "ステップ 3: ✓ 成功" in output
            
            # Verify all step outputs are shown
            assert "Step 1" in output
            assert "Step 2" in output
            assert "Step 3" in output
            
        finally:
            sys.stdout = old_stdout


class TestMainE2EMockErrorCases:
    """E2E error case tests for main() function using mock drivers"""
    
    def setup_method(self):
        """Setup test fixtures with mock operations"""
        self.operations = build_mock_operations()
        self.mock_file_driver = self.operations.resolve('file_driver')
        self.mock_shell_driver = self.operations.resolve('shell_driver')
        self.mock_python_driver = self.operations.resolve('python_driver')
        
        # Clear any previous state
        self.mock_file_driver.files.clear()
        self.mock_file_driver.contents.clear()
        self.mock_file_driver.operations.clear()
        self.mock_shell_driver.calls.clear()
        self.mock_shell_driver.expected_results.clear()
        self.mock_python_driver.reset()
        
        # Create directory structure in mock filesystem
        self.mock_file_driver.files.add(self.mock_file_driver.base_dir / Path("contest_env"))
        self.mock_file_driver.files.add(self.mock_file_driver.base_dir / Path("contest_env/python"))
        
        # Set default mock behavior for Python commands
        self.mock_python_driver.set_default_result(
            stdout="Mock python execution",
            stderr="",
            returncode=0
        )
        
        # Mock webbrowser.open to prevent actual browser opening
        self.mock_python_driver.set_expected_result(
            "webbrowser.open",
            stdout="Mock browser opened",
            stderr="",
            returncode=0
        )
    
    def test_main_missing_system_info_file(self):
        """Test main() behavior when system_info.json is missing"""
        # Don't create system_info.json - this should cause an error during parsing
        
        # Parse arguments - this should handle missing system_info gracefully
        args = ["python", "local", "test", "abc300", "a"]
        
        # This might fail during parse_user_input or during main execution
        # depending on how the system handles missing system_info
        try:
            context = parse_user_input(args, self.operations)
            # If parsing succeeds, main should handle the missing information
            result = main(context, self.operations)
            # If we get here, verify the behavior is reasonable
            assert isinstance(result, WorkflowExecutionResult)
        except (FileNotFoundError, ValueError, Exception) as e:
            # Expected - missing system_info should cause an error
            assert "system_info" in str(e).lower() or "ファイルが見つかりません" in str(e)
    
    def test_main_invalid_json_format(self):
        """Test main() behavior with invalid JSON in config files"""
        # Create invalid JSON in system_info.json
        self.mock_file_driver._create_impl(
            "system_info.json",
            "{ invalid json content"
        )
        
        args = []
        
        # Should fail during parsing due to invalid JSON
        with pytest.raises((json.JSONDecodeError, ValueError)):
            context = parse_user_input(args, self.operations)
    
    def test_main_step_failure_with_continue(self):
        """Test main() with a step that fails but is allowed to continue"""
        # Setup system_info.json
        system_info = {
            "command": "test",
            "language": "python",
            "env_type": "local",
            "contest_name": "abc300",
            "problem_name": "a"
        }
        self.mock_file_driver._create_impl(
            "system_info.json",
            json.dumps(system_info, ensure_ascii=False, indent=2)
        )
        
        # Setup env.json with a command that allows failure
        env_config = {
            "test": {
                "python": {
                    "commands": [
                        {
                            "type": "shell", 
                            "cmd": ["false"],  # Command that always fails
                            "allow_failure": True
                        },
                        {
                            "type": "shell",
                            "cmd": ["echo", "continuing after failure"]
                        }
                    ]
                }
            }
        }
        self.mock_file_driver._create_impl(
            "contest_env/python/env.json",
            json.dumps(env_config, ensure_ascii=False, indent=2)
        )
        
        # Mock shell executions
        self.mock_shell_driver.set_expected_result(
            "false",
            stdout="",
            stderr="false command failed",
            returncode=1
        )
        self.mock_shell_driver.set_expected_result(
            "echo continuing after failure",
            stdout="continuing after failure\n",
            stderr="",
            returncode=0
        )
        
        # Parse and execute
        args = []
        context = parse_user_input(args, self.operations)
        
        captured_output = StringIO()
        old_stdout = sys.stdout
        sys.stdout = captured_output
        
        try:
            result = main(context, self.operations)
            
            # Should succeed overall despite one step failing
            assert result.success is True
            assert len(result.results) == 2
            
            output = captured_output.getvalue()
            
            # Should show the allowed failure
            assert "⚠️ 失敗 (許可済み)" in output
            assert "✓ 成功" in output
            assert "continuing after failure" in output
            
        finally:
            sys.stdout = old_stdout