#!/usr/bin/env python3

import json
import sys
from io import StringIO

from src.context.user_input_parser import parse_user_input
from src.infrastructure.build_infrastructure import build_mock_operations
from src.main import main

# Create mock operations
operations = build_mock_operations()
mock_file_driver = operations.resolve('file_driver')
mock_shell_driver = operations.resolve('shell_driver')

# Clear any previous state
mock_file_driver.files.clear()
mock_file_driver.contents.clear()
mock_file_driver.operations.clear()
mock_shell_driver.calls.clear()
mock_shell_driver.expected_results.clear()

# Setup system_info.json with non-existent script
system_info = {
    "command": "test",
    "language": "python",
    "env_type": "local",
    "contest_name": "abc999",
    "problem_name": "z"
}
mock_file_driver._create_impl(
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
mock_file_driver._create_impl(
    "contest_env/python/env.json",
    json.dumps(env_config, ensure_ascii=False, indent=2)
)

# Mock shell execution to simulate file not found - try different patterns
mock_shell_driver.set_expected_result(
    "python",  # Try just matching on "python"
    stdout="",
    stderr="python: can't open file 'contest_stock/abc999/z/main.py': [Errno 2] No such file or directory",
    returncode=2
)

# Parse arguments and create context
args = []
context = parse_user_input(args, operations)

# Capture stdout for verification
captured_output = StringIO()
old_stdout = sys.stdout
sys.stdout = captured_output

try:
    # Execute main function
    result = main(context, operations)
    print(f"Result success: {result.success}")
    print(f"Number of results: {len(result.results)}")
    for i, res in enumerate(result.results):
        print(f"Result {i}: success={res.success}, returncode={getattr(res, 'returncode', 'N/A')}")

    # Check what commands were actually called
    print(f"Shell calls made: {len(mock_shell_driver.calls)}")
    for i, call in enumerate(mock_shell_driver.calls):
        print(f"Call {i}: {call}")

except Exception as e:
    print(f"Exception raised: {e}")

finally:
    sys.stdout = old_stdout

output = captured_output.getvalue()
print("Captured output:")
print(output)
