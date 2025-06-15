#!/usr/bin/env python3
"""Debug script to specifically test the error case you mentioned"""

import tempfile
from pathlib import Path

from src.application.factories.unified_request_factory import FileRequestStrategy
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.utils.debug_logger import DebugLogger
from src.workflow.step.simple_step_runner import ExecutionContext, create_step
from src.workflow.step.step import StepType


def test_copy_to_copytree_conversion():
    """Test to see if COPY steps are somehow being converted to COPYTREE"""

    # Create temporary directories matching your error
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)

        # Create exact structure from your error
        template_dir = tmpdir / "contest_template" / "python"
        template_dir.mkdir(parents=True)

        current_dir = tmpdir / "contest_current"
        current_dir.mkdir(parents=True)

        # Create the source file mentioned in your error
        source_file = template_dir / "main.py"
        source_file.write_text("print('Hello World')")

        print("Test setup:")
        print(f"  Source: {source_file} (exists: {source_file.exists()})")
        print(f"  Dest dir: {current_dir} (exists: {current_dir.exists()})")

        # Create execution context with file patterns like the actual config
        context = ExecutionContext(
            contest_name="abc300",
            problem_name="a",
            language="python",
            workspace_path=str(tmpdir),
            contest_current_path=str(current_dir),
            contest_template_path=str(tmpdir / "contest_template"),
            file_patterns={
                "contest_files": ["main.py", "*.py"],
                "test_files": ["test/*.in", "test/*.out"]
            }
        )

        # Test the exact JSON step that should be causing the issue
        json_step = {
            "name": "ソースファイルをワークスペースにコピー",
            "type": "copy",
            "allow_failure": False,
            "show_output": False,
            "cmd": ["contest_template/python/main.py", "contest_current/main.py"]
        }

        print("\n=== Testing problematic JSON step ===")
        print(f"JSON step: {json_step}")

        # Create step from JSON (this is where conversion might happen)
        step = create_step(json_step, context)
        print(f"Created StepType: {step.type}")
        print(f"Step cmd after expansion: {step.cmd}")

        # Check if the file pattern expansion affected anything
        if step.type != StepType.COPY:
            print(f"❌ ERROR: Step type was changed from COPY to {step.type}!")
        else:
            print("✅ Step type remains COPY")

        # Test FileRequestStrategy mapping
        strategy = FileRequestStrategy()

        if strategy.can_handle(step.type):
            env_manager = EnvironmentManager("local")
            request = strategy.create_request(step, context, env_manager)

            if request:
                print(f"Created FileOpType: {request.op}")

                if request.op.name != "COPY":
                    print(f"❌ ERROR: FileOpType was changed to {request.op.name}!")
                else:
                    print("✅ FileOpType remains COPY")

                # Test the debug output that was showing FILE.COPYTREE
                debug_logger = DebugLogger({})
                debug_logger.enable()

                from src.workflow.builder.execution.execution_debug import debug_request_before_execution

                # Create a mock node to test debug output
                class MockNode:
                    def __init__(self, request):
                        self.request = request

                node = MockNode(request)

                print("\n=== Testing debug output ===")
                try:
                    debug_request_before_execution(debug_logger, node, "test_node")
                except Exception as e:
                    print(f"Debug output failed: {e}")

            else:
                print("❌ ERROR: Failed to create request")
        else:
            print(f"❌ ERROR: Strategy cannot handle StepType: {step.type}")

if __name__ == "__main__":
    test_copy_to_copytree_conversion()
