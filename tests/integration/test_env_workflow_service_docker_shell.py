import pytest
from src.env.env_workflow_service import EnvWorkflowService
from src.context.execution_context import ExecutionContext
import os
from src.operations.di_container import DIContainer

def test_env_workflow_service_docker_shell_no_driver():
    # ダミーenv_json（docker環境用）
    env_json = {
        "python": {
            "commands": {
                "run": {
                    "steps": [
                        {"type": "shell", "cmd": ["echo", "hello"]}
                    ]
                }
            }
        }
    }
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="docker",  # docker環境
        env_json=env_json,
        contest_current_path="contests/abc001"
    )
    service = EnvWorkflowService.from_context(env_context, di_container=DIContainer())
    with pytest.raises(ValueError) as excinfo:
        service.run_workflow()
    assert "not registered" in str(excinfo.value) 