import pytest
from src.env.env_workflow_service import EnvWorkflowService
from src.context.execution_context import ExecutionContext
from src.env.env_resource_controller import EnvResourceController
from src.env.resource.file.local_file_handler import LocalFileHandler
from src.env.resource.run.local_run_handler import LocalRunHandler
from src.env.resource.utils.const_handler import ConstHandler
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
        contest_current_path="contests/abc001",
        workspace_path="/tmp/workspace"
    )
    const_handler = ConstHandler(env_context)
    file_handler = LocalFileHandler(env_context, const_handler)
    run_handler = LocalRunHandler(env_context, const_handler)
    controller = EnvResourceController(env_context, file_handler, run_handler, const_handler)
    service = EnvWorkflowService(env_context, controller, di_container=DIContainer())
    with pytest.raises(ValueError) as excinfo:
        service.run_workflow()
    assert "not registered" in str(excinfo.value) 