import pytest
from src.env.env_workflow_service import EnvWorkflowService
from src.context.execution_context import ExecutionContext
import os

def test_env_workflow_service_docker_no_driver():
    # ダミーenv_json（docker環境用）
    env_json = {
        "python": {
            "commands": {
                "run": {
                    "steps": [
                        {"type": "oj", "cmd": ["echo", "hello"]}
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
    run_steps_dict_list = [
        {"type": "oj", "cmd": ["echo", "hello"]}
    ]
    service = EnvWorkflowService.from_context(env_context, workspace_path=os.getcwd())
    with pytest.raises(ValueError) as excinfo:
        service.run_workflow(run_steps_dict_list, driver=None)
    assert str(excinfo.value) == "DockerRequest.execute()にはdriverが必須です" 