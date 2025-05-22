import pytest
from src.env.env_workflow_service import EnvWorkflowService
from src.context.execution_context import ExecutionContext
import os

def test_env_workflow_service_shell_no_driver():
    # ダミーenv_json（最低限languageが必要）
    env_json = {"python": {}}
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=env_json,
        contest_current_path="contests/abc001"
    )
    run_steps_dict_list = [
        {"type": "shell", "cmd": ["echo", "hello"]}
    ]
    # workspace_pathを明示的に指定
    service = EnvWorkflowService.from_context(env_context, workspace_path=os.getcwd())
    with pytest.raises(ValueError) as excinfo:
        service.run_workflow(run_steps_dict_list, driver=None)
    assert str(excinfo.value) == "ShellRequest.execute()にはdriverが必須です" 