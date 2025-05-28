import pytest
from src.env.env_workflow_service import EnvWorkflowService
from src.context.execution_context import ExecutionContext
from src.env.env_resource_controller import EnvResourceController
from src.env.resource.file.local_file_handler import LocalFileHandler
from src.env.resource.run.local_run_handler import LocalRunHandler
from src.env.resource.utils.const_handler import ConstHandler
from src.operations.di_container import DIContainer
from src.context.config_resolver import ConfigResolver

def test_env_workflow_service_shell_no_driver():
    # ダミーenv_json（最低限languageが必要）
    env_json = {
        "python": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "commands": {
                "run": {
                    "steps": [
                        {"type": "shell", "cmd": ["echo", "hello"]}
                    ]
                }
            },
            "source_file_name": "main.py",
            "contest_env_path": "env",
            "contest_template_path": "template",
            "contest_temp_path": "temp",
            "language_id": 2001,
            "env_types": {"local": {}}
        }
    }
    resolver = ConfigResolver.from_dict(env_json)
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=env_json,
        resolver=resolver
    )
    const_handler = ConstHandler(env_context)
    file_handler = LocalFileHandler(env_context, const_handler)
    run_handler = LocalRunHandler(env_context, const_handler)
    controller = EnvResourceController(env_context, file_handler, run_handler, const_handler)
    operations = DIContainer()
    from src.env.factory.shell_command_request_factory import ShellCommandRequestFactory
    operations.register("ShellCommandRequestFactory", lambda: ShellCommandRequestFactory)
    operations.register("shell_driver", lambda: None)
    service = EnvWorkflowService(env_context, operations)
    with pytest.raises(ValueError):
        service.run_workflow()

def test_source_file_name_is_none_when_not_set():
    env_json = {
        "python": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "commands": {
                "run": {
                    "steps": [
                        {"type": "shell", "cmd": ["echo", "hello"]}
                    ]
                }
            },
            # source_file_nameは無し
            "contest_env_path": "env",
            "contest_template_path": "template",
            "contest_temp_path": "temp",
            "language_id": 2001,
            "env_types": {"local": {}}
        }
    }
    resolver = ConfigResolver.from_dict(env_json)
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=env_json,
        resolver=resolver
    )
    const_handler = ConstHandler(env_context)
    with pytest.raises(KeyError):
        _ = const_handler.source_file_name

def test_source_file_name_must_not_be_none():
    env_json = {
        "python": {
            "workspace_path": "/tmp/workspace",
            "contest_current_path": "contests/abc001",
            "commands": {
                "run": {
                    "steps": [
                        {"type": "shell", "cmd": ["echo", "hello"]}
                    ]
                }
            },
            "source_file_name": "main.py",
            "contest_env_path": "env",
            "contest_template_path": "template",
            "contest_temp_path": "temp",
            "language_id": 2001,
            "env_types": {"local": {}}
        }
    }
    resolver = ConfigResolver.from_dict(env_json)
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=env_json,
        resolver=resolver
    )
    const_handler = ConstHandler(env_context)
    assert const_handler.source_file_name is not None, "source_file_name must not be None! env_jsonにsource_file_nameがありません" 