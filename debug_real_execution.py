#!/usr/bin/env python3
"""Debug script to check what's happening in real execution"""

import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from src.context.user_input_parser import parse_user_input
from src.infrastructure.build_infrastructure import build_operations


def debug_real_execution():
    """Debug the real execution flow to see what's wrong with template expansion"""

    # Create operations container like the real application
    operations = build_operations()

    args = ["python", "test", "abc300", "a"]

    print("=== Debugging Real Execution ===")
    print(f"Args: {args}")

    try:
        # Parse user input like the real application
        context = parse_user_input(args, operations)

        print("\nContext created:")
        print(f"  Type: {type(context)}")
        print(f"  Language: {context.language}")
        print(f"  Command type: {context.command_type}")
        print(f"  Contest name: {context.contest_name}")
        print(f"  Problem name: {context.problem_name}")

        # Check the template dictionary
        template_dict = context.to_dict()
        print("\nTemplate dictionary:")
        for key, value in template_dict.items():
            print(f"  {key}: {value}")

        print("\nSpecific checks:")
        print(f"  source_file_name: {template_dict.get('source_file_name', 'NOT_FOUND')}")
        print(f"  contest_current_path: {template_dict.get('contest_current_path', 'NOT_FOUND')}")
        print(f"  workspace_path: {template_dict.get('workspace_path', 'NOT_FOUND')}")

        # Test specific template expansions
        test_templates = [
            "{source_file_name}",
            "{contest_current_path}/{source_file_name}",
            "{workspace_path}/{source_file_name}"
        ]

        print("\n=== Testing template expansion ===")
        for template in test_templates:
            try:
                expanded = context.format_string(template)
                print(f"  '{template}' -> '{expanded}'")

                if template.endswith("/{source_file_name}") and expanded.endswith("/"):
                    print("    ❌ ERROR: Ends with '/', source_file_name not expanded")
                elif "{source_file_name}" in template and "{source_file_name}" in expanded:
                    print("    ❌ ERROR: Template not replaced")
                else:
                    print("    ✅ Template expanded correctly")
            except Exception as e:
                print(f"  '{template}' -> ERROR: {e}")

        # Check env_json structure
        print("\n=== Checking env_json structure ===")
        if hasattr(context, 'env_json') and context.env_json:
            print(f"env_json type: {type(context.env_json)}")
            print(f"env_json keys: {list(context.env_json.keys()) if isinstance(context.env_json, dict) else 'Not a dict'}")

            # Look for test command configuration
            if isinstance(context.env_json, dict):
                if 'commands' in context.env_json:
                    print(f"commands keys: {list(context.env_json['commands'].keys())}")
                    if 'test' in context.env_json['commands']:
                        print(f"test command: {context.env_json['commands']['test']}")

                # Look for source_file_name in various places
                if 'source_file_name' in context.env_json:
                    print(f"source_file_name (top level): {context.env_json['source_file_name']}")

                if 'python' in context.env_json and isinstance(context.env_json['python'], dict):
                    if 'source_file_name' in context.env_json['python']:
                        print(f"source_file_name (in python): {context.env_json['python']['source_file_name']}")
        else:
            print("No env_json found")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_real_execution()
