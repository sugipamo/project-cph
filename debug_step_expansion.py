#!/usr/bin/env python3
"""Debug script to test step creation and expansion"""

import os
import sys

sys.path.insert(0, os.path.abspath('.'))

from src.context.user_input_parser import parse_user_input
from src.infrastructure.build_infrastructure import build_operations
from src.workflow.step.simple_step_runner import create_step, expand_template


def debug_step_expansion():
    """Debug the step creation and template expansion"""

    # Create operations container like the real application
    operations = build_operations()

    args = ["python", "test", "abc300", "a"]

    print("=== Debugging Step Creation and Expansion ===")
    print(f"Args: {args}")

    try:
        # Parse user input like the real application
        context = parse_user_input(args, operations)

        print("\nContext created:")
        print(f"  Type: {type(context)}")
        print(f"  Has format_string: {hasattr(context, 'format_string')}")

        # Test the expand_template function directly
        test_templates = [
            "{source_file_name}",
            "{contest_current_path}/{source_file_name}",
            "{workspace_path}/{source_file_name}"
        ]

        print("\n=== Testing expand_template function directly ===")
        for template in test_templates:
            try:
                expanded = expand_template(template, context)
                print(f"  '{template}' -> '{expanded}'")

                if template.endswith("/{source_file_name}") and expanded.endswith("/"):
                    print("    ❌ ERROR: Ends with '/', source_file_name not expanded")
                elif "{source_file_name}" in template and "{source_file_name}" in expanded:
                    print("    ❌ ERROR: Template not replaced")
                else:
                    print("    ✅ Template expanded correctly")
            except Exception as e:
                print(f"  '{template}' -> ERROR: {e}")

        # Test the actual create_step function with real JSON
        print("\n=== Testing create_step function with real JSON ===")
        json_step = {
            "name": "ソースファイルをワークスペースにコピー",
            "type": "copy",
            "allow_failure": False,
            "show_output": False,
            "cmd": ["{contest_current_path}/{source_file_name}", "{workspace_path}/{source_file_name}"]
        }

        print(f"Input JSON step: {json_step}")

        try:
            step = create_step(json_step, context)
            print("Created step:")
            print(f"  Type: {step.type}")
            print(f"  Name: {step.name}")
            print(f"  Cmd: {step.cmd}")
            print(f"  Allow failure: {step.allow_failure}")

            # Check for problematic patterns
            for i, cmd_part in enumerate(step.cmd):
                if cmd_part.endswith("/") and not cmd_part.endswith("./"):
                    print(f"    ❌ ERROR: cmd[{i}] ends with '/', indicating missing source_file_name: '{cmd_part}'")
                else:
                    print(f"    ✅ cmd[{i}] looks correct: '{cmd_part}'")
        except Exception as e:
            print(f"Step creation failed: {e}")
            import traceback
            traceback.print_exc()

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_step_expansion()
