#!/usr/bin/env python3
"""Debug script to test full execution flow that might be causing the COPY->COPYTREE conversion"""

import tempfile
from pathlib import Path

from src.application.factories.unified_request_factory import FileRequestStrategy
from src.infrastructure.drivers.file.local_file_driver import LocalFileDriver
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.workflow.step.simple_step_runner import ExecutionContext, create_step


def test_full_execution_flow():
    """Test the full execution flow to see where COPY might become COPYTREE"""

    # Create temporary directories for testing
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create source structure
        template_dir = tmpdir / "contest_template" / "python"
        template_dir.mkdir(parents=True)

        # Create source file
        source_file = template_dir / "main.py"
        source_file.write_text("print('Hello World')")

        # Create destination directory
        current_dir = tmpdir / "contest_current"
        current_dir.mkdir(parents=True)

        print("Created test structure:")
        print(f"  Source file: {source_file}")
        print(f"  Destination dir: {current_dir}")
        print(f"  Source exists: {source_file.exists()}")
        print(f"  Source is file: {source_file.is_file()}")
        print(f"  Dest dir exists: {current_dir.exists()}")

        # Create execution context
        context = ExecutionContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            workspace_path=str(tmpdir),
            contest_current_path=str(current_dir),
            contest_template_path=str(tmpdir / "contest_template")
        )

        # Test JSON step with type "copy"
        json_step = {
            "type": "copy",
            "cmd": [str(source_file), str(current_dir / "main.py")]
        }

        print("\n=== Testing Step Creation ===")
        print(f"JSON step: {json_step}")

        # Create step from JSON
        step = create_step(json_step, context)
        print(f"Created StepType: {step.type}")
        print(f"Step cmd: {step.cmd}")

        # Test FileRequestStrategy mapping
        print("\n=== Testing FileRequest Creation ===")
        strategy = FileRequestStrategy()

        if strategy.can_handle(step.type):
            print(f"Strategy can handle StepType: {step.type}")

            # Create request
            env_manager = EnvironmentManager("local")
            request = strategy.create_request(step, context, env_manager)

            if request:
                print(f"Created FileOpType: {request.op}")
                print(f"FileOpType name: {request.op.name}")
                print(f"Request path: {request.path}")
                print(f"Request dst_path: {request.dst_path}")

                # Test actual execution
                print("\n=== Testing Actual Execution ===")
                try:
                    file_driver = LocalFileDriver(tmpdir)
                    result = request.execute_operation(file_driver)
                    print(f"Execution result: {result}")
                    print(f"Execution success: {result.success}")

                    # Check if destination file was created
                    dest_file = current_dir / "main.py"
                    print(f"Destination file exists: {dest_file.exists()}")
                    if dest_file.exists():
                        print(f"Destination file content: {dest_file.read_text()}")

                except Exception as e:
                    print(f"ERROR during execution: {e}")
                    print(f"Exception type: {type(e)}")
                    import traceback
                    traceback.print_exc()

            else:
                print("ERROR: Failed to create request")
        else:
            print(f"ERROR: Strategy cannot handle StepType: {step.type}")

if __name__ == "__main__":
    test_full_execution_flow()
