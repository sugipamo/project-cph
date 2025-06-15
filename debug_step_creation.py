#!/usr/bin/env python3
"""Debug script to test step creation from JSON"""

from src.application.factories.unified_request_factory import FileRequestStrategy
from src.infrastructure.environment.environment_manager import EnvironmentManager
from src.workflow.step.simple_step_runner import ExecutionContext, create_step


def test_copy_step_creation():
    """Test that 'copy' JSON step creates correct StepType and FileOpType"""

    # Create execution context
    context = ExecutionContext(
        contest_name="abc300",
        problem_name="a",
        language="python",
        workspace_path="/tmp/workspace",
        contest_current_path="/tmp/contest_current",
        contest_template_path="/tmp/contest_template"
    )

    # Test JSON step with type "copy"
    json_step = {
        "type": "copy",
        "cmd": ["contest_template/python/main.py", "contest_current/main.py"]
    }

    print("=== Testing Step Creation ===")
    print(f"JSON step: {json_step}")

    # Create step from JSON
    step = create_step(json_step, context)
    print(f"Created StepType: {step.type}")
    print(f"StepType value: {step.type.value}")
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
        else:
            print("ERROR: Failed to create request")
    else:
        print(f"ERROR: Strategy cannot handle StepType: {step.type}")

if __name__ == "__main__":
    test_copy_step_creation()
