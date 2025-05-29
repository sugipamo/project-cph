import pytest
from src.env.env_workflow_service import EnvWorkflowService
from src.context.execution_context import ExecutionContext
from src.env.env_resource_controller import EnvResourceController
from src.env.resource.file.local_file_handler import LocalFileHandler
from src.env.resource.run.local_run_handler import LocalRunHandler
from src.env.resource.utils.const_handler import ConstHandler
from src.operations.di_container import DIContainer
from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.env.factory.oj_command_request_factory import OjCommandRequestFactory
from src.env.factory.docker_command_request_factory import DockerCommandRequestFactory
from src.context.resolver.config_resolver import create_config_root_from_dict

def test_env_workflow_service_docker_no_driver():
    # ダミーenv_json（docker環境用）
    env_json = {
        "python": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "commands": {
                "run": {
                    "steps": [
                        {"type": "oj", "cmd": ["echo", "hello"]}
                    ]
                }
            },
            "cph_ojtools": "dummy_container",
            "contest_env_path": "env",
            "contest_template_path": "template",
            "contest_temp_path": "temp",
            "source_file_name": "main.py",
            "language_id": 2001,
            "env_types": {"docker": {}}
        }
    }
    root = create_config_root_from_dict(env_json)
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="docker",  # docker環境
        env_json=env_json,
        resolver=root
    )
    env_context.oj_dockerfile = "FROM python:3.9\nRUN echo oj"
    const_handler = ConstHandler(env_context)
    file_handler = LocalFileHandler(env_context, const_handler)
    run_handler = LocalRunHandler(env_context, const_handler)
    controller = EnvResourceController(env_context, file_handler, run_handler, const_handler)
    operations = DIContainer()
    operations.register("DockerRequest", lambda: DockerRequest)
    operations.register("DockerOpType", lambda: DockerOpType)
    operations.register("OjCommandRequestFactory", lambda: OjCommandRequestFactory)
    operations.register("DockerCommandRequestFactory", lambda: DockerCommandRequestFactory)
    operations.register("docker_driver", lambda: None)
    service = EnvWorkflowService(env_context, operations)
    with pytest.raises(ValueError):
        service.run_workflow() 