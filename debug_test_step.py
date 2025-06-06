#!/usr/bin/env python3

import json
import sys
from pathlib import Path
from io import StringIO

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.main import main
from src.operations.build_operations import build_mock_operations
from src.context.user_input_parser import parse_user_input

def debug_main_execution():
    """Debug single step main execution"""
    # Setup mock operations
    operations = build_mock_operations()
    mock_file_driver = operations.resolve('file_driver')
    mock_shell_driver = operations.resolve('shell_driver')
    mock_python_driver = operations.resolve('python_driver')
    
    # Clear any previous state
    mock_file_driver.files.clear()
    mock_file_driver.contents.clear()
    mock_file_driver.operations.clear()
    mock_shell_driver.calls.clear()
    mock_shell_driver.expected_results.clear()
    mock_python_driver.reset()
    
    # Setup system_info.json
    system_info = {
        "command": "test",
        "language": "python",
        "env_type": "local",
        "contest_name": "abc300",
        "problem_name": "a"
    }
    mock_file_driver._create_impl(
        "system_info.json",
        json.dumps(system_info, ensure_ascii=False, indent=2)
    )
    
    # Create contest_env directory in mock filesystem
    mock_file_driver.files.add(mock_file_driver.base_dir / Path("contest_env"))
    mock_file_driver.files.add(mock_file_driver.base_dir / Path("contest_env/python"))
    
    # Setup env.json for Python
    env_config = {
        "python": {
            "aliases": ["py"],
            "commands": {
                "test": {
                    "aliases": ["t"],
                    "steps": [
                        {"type": "shell", "cmd": ["echo", "test output"]}
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
    mock_file_driver._create_impl(
        "contest_env/python/env.json",
        json.dumps(env_config, ensure_ascii=False, indent=2)
    )
    
    # Mock shell execution 
    mock_shell_driver.set_expected_result(
        "echo test output",
        stdout="test output\n",
        stderr="",
        returncode=0
    )
    
    # Parse arguments and create context
    print("=== Parsing user input ===")
    args = []
    try:
        context = parse_user_input(args, operations)
        print(f"✓ Context created successfully")
        print(f"  command_type: {context.command_type}")
        print(f"  language: {context.language}")
        print(f"  env_json is None: {context.env_json is None}")
        if context.env_json:
            print(f"  env_json keys: {list(context.env_json.keys())}")
            if context.language in context.env_json:
                lang_config = context.env_json[context.language]
                print(f"  {context.language} commands: {list(lang_config.get('commands', {}).keys())}")
        else:
            print("  Checking if contest_env files exist:")
            env_exists = mock_file_driver._exists_impl("contest_env")
            print(f"    contest_env exists: {env_exists}")
            python_env_exists = mock_file_driver._exists_impl("contest_env/python/env.json")
            print(f"    contest_env/python/env.json exists: {python_env_exists}")
            if python_env_exists:
                from src.operations.file.file_request import FileRequest
                from src.operations.file.file_op_type import FileOpType
                req = FileRequest(FileOpType.READ, "contest_env/python/env.json")
                result = req.execute(driver=mock_file_driver)
                print(f"    contest_env/python/env.json content: {result.content[:200]}...")
    except Exception as e:
        print(f"✗ Failed to create context: {e}")
        import traceback
        traceback.print_exc()
        return
    
    # Try main execution
    print("\n=== Executing main ===")
    try:
        result = main(context, operations)
        print(f"✓ Main executed successfully")
        print(f"  success: {result.success}")
        print(f"  results count: {len(result.results)}")
        print(f"  errors: {result.errors}")
        print(f"  warnings: {result.warnings}")
    except Exception as e:
        print(f"✗ Main execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_main_execution()