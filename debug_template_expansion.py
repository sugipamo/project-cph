#!/usr/bin/env python3
"""Debug script to specifically test template expansion and source_file_name"""

import os

# Test the new configuration system
from src.configuration.integration.user_input_parser_integration import create_new_execution_context
from src.infrastructure.config.json_config_loader import JsonConfigLoader
from src.workflow.step.simple_step_runner import create_step


def test_template_expansion():
    """Test template expansion with focus on source_file_name"""

    # Create a mock env_json similar to what would be loaded
    env_json = {
        "python": {
            "language_id": "python",
            "source_file_name": "main.py",
            "run_command": "python3",
            "commands": {
                "test": {
                    "steps": [
                        {
                            "name": "ソースファイルをワークスペースにコピー",
                            "type": "copy",
                            "cmd": ["{contest_template_path}/{language}/{source_file_name}", "{contest_current_path}/{source_file_name}"]
                        }
                    ]
                }
            }
        }
    }

    print("=== Testing template expansion with new configuration system ===")

    # Create ExecutionContextAdapter using new system
    context = create_new_execution_context(
        command_type="test",
        language="python",
        contest_name="abc300",
        problem_name="a",
        env_type="local",
        env_json=env_json
    )

    print("Context created:")
    print(f"  Language: {context.language}")
    print(f"  Command type: {context.command_type}")
    print(f"  Contest name: {context.contest_name}")
    print(f"  Problem name: {context.problem_name}")

    # Check the template dictionary
    template_dict = context.to_dict()
    print("\nTemplate dictionary:")
    for key, value in template_dict.items():
        print(f"  {key}: {value}")

    print(f"\nSpecific check for source_file_name: {template_dict.get('source_file_name', 'NOT_FOUND')}")

    # Test template expansion directly
    test_templates = [
        "{source_file_name}",
        "{contest_current_path}/{source_file_name}",
        "{contest_template_path}/{language}/{source_file_name}",
        "{workspace_path}/{source_file_name}"
    ]

    print("\n=== Testing template expansion ===")
    for template in test_templates:
        try:
            expanded = context.format_string(template)
            print(f"  '{template}' -> '{expanded}'")

            # Check for the problematic patterns that would cause COPY -> COPYTREE
            if template.endswith("/{source_file_name}") and expanded.endswith("/"):
                print("    ❌ ERROR: source_file_name not expanded, ends with '/'")
            elif "{source_file_name}" in template and "{source_file_name}" in expanded:
                print("    ❌ ERROR: source_file_name template not replaced")
            else:
                print("    ✅ Template expanded correctly")
        except Exception as e:
            print(f"  '{template}' -> ERROR: {e}")

    # Test actual step creation with template expansion
    print("\n=== Testing step creation with template expansion ===")
    json_step = {
        "name": "ソースファイルをワークスペースにコピー",
        "type": "copy",
        "cmd": ["{contest_template_path}/{language}/{source_file_name}", "{contest_current_path}/{source_file_name}"]
    }

    print(f"Original JSON step cmd: {json_step['cmd']}")

    try:
        step = create_step(json_step, context)
        print(f"Expanded step cmd: {step.cmd}")

        # Check if any paths end with just "/" which would indicate missing source_file_name
        for i, cmd_part in enumerate(step.cmd):
            if cmd_part.endswith("/") and not cmd_part.endswith("./"):
                print(f"  ❌ ERROR: cmd[{i}] ends with '/', indicating missing source_file_name: '{cmd_part}'")
            else:
                print(f"  ✅ cmd[{i}] looks correct: '{cmd_part}'")

    except Exception as e:
        print(f"Step creation failed: {e}")

def test_json_config_loader():
    """Test JsonConfigLoader to see what it returns"""
    print("\n=== Testing JsonConfigLoader ===")

    # Test with contest_env directory
    contest_env_dir = "contest_env"
    if os.path.exists(contest_env_dir):
        loader = JsonConfigLoader(contest_env_dir)

        try:
            python_config = loader.get_language_config("python")
            print("Python config from JsonConfigLoader:")
            print(f"  Type: {type(python_config)}")

            if python_config:
                # Check if it's a dict and has source_file_name
                if isinstance(python_config, dict):
                    print(f"  Keys: {list(python_config.keys())}")

                    # Look for source_file_name in various places
                    if "source_file_name" in python_config:
                        print(f"  source_file_name (top level): {python_config['source_file_name']}")

                    if "python" in python_config and isinstance(python_config["python"], dict):
                        if "source_file_name" in python_config["python"]:
                            print(f"  source_file_name (in python): {python_config['python']['source_file_name']}")

                    if "runtime" in python_config and isinstance(python_config["runtime"], dict):
                        if "source_file_name" in python_config["runtime"]:
                            print(f"  source_file_name (in runtime): {python_config['runtime']['source_file_name']}")
                else:
                    print(f"  Config is not a dict: {python_config}")
            else:
                print("  No config returned for python")

        except Exception as e:
            print(f"  Error loading python config: {e}")
    else:
        print("  contest_env directory not found")

if __name__ == "__main__":
    test_template_expansion()
    test_json_config_loader()
