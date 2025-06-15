#!/usr/bin/env python3
"""Debug script to check what context.to_format_dict() returns"""

import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from src.context.user_input_parser import parse_user_input
from src.infrastructure.build_infrastructure import build_operations


def debug_format_method():
    """Debug the context.to_format_dict() method specifically"""

    # Create operations container like the real application
    operations = build_operations()

    args = ["python", "test", "abc300", "a"]

    print("=== Debugging to_format_dict() method ===")
    print(f"Args: {args}")

    try:
        # Parse user input like the real application
        context = parse_user_input(args, operations)

        print("\nContext created:")
        print(f"  Type: {type(context)}")
        print(f"  Has to_format_dict: {hasattr(context, 'to_format_dict')}")

        if hasattr(context, 'to_format_dict'):
            format_dict = context.to_format_dict()
            print("\nto_format_dict() result:")
            print(f"  Type: {type(format_dict)}")
            print(f"  Keys: {list(format_dict.keys()) if isinstance(format_dict, dict) else 'Not a dict'}")

            if isinstance(format_dict, dict):
                print(f"  source_file_name: {format_dict.get('source_file_name', 'NOT_FOUND')}")
                print(f"  contest_current_path: {format_dict.get('contest_current_path', 'NOT_FOUND')}")
                print(f"  workspace_path: {format_dict.get('workspace_path', 'NOT_FOUND')}")

                # Test the format_values_with_context_dict function directly
                from src.context.formatters.context_formatter import format_values_with_context_dict

                test_cmd = ["{contest_current_path}/{source_file_name}", "{workspace_path}/{source_file_name}"]
                print("\nTesting format_values_with_context_dict:")
                print(f"  Input cmd: {test_cmd}")

                formatted_cmd = format_values_with_context_dict(test_cmd, format_dict)
                print(f"  Formatted cmd: {formatted_cmd}")

                # Check for problematic patterns
                for i, cmd_part in enumerate(formatted_cmd):
                    if cmd_part.endswith("/") and not cmd_part.endswith("./"):
                        print(f"    ❌ ERROR: cmd[{i}] ends with '/', indicating missing source_file_name: '{cmd_part}'")
                    else:
                        print(f"    ✅ cmd[{i}] looks correct: '{cmd_part}'")
        else:
            print("  ERROR: Context does not have to_format_dict method")

        # Also test the to_dict method for comparison
        if hasattr(context, 'to_dict'):
            to_dict_result = context.to_dict()
            print("\nto_dict() result for comparison:")
            print(f"  Type: {type(to_dict_result)}")
            if isinstance(to_dict_result, dict):
                print(f"  source_file_name: {to_dict_result.get('source_file_name', 'NOT_FOUND')}")
                print(f"  contest_current_path: {to_dict_result.get('contest_current_path', 'NOT_FOUND')}")
                print(f"  workspace_path: {to_dict_result.get('workspace_path', 'NOT_FOUND')}")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_format_method()
