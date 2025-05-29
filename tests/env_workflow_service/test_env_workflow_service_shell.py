import pytest
from src.env.env_workflow_service import EnvWorkflowService
from src.context.execution_context import ExecutionContext
from src.env.env_resource_controller import EnvResourceController
from src.env.resource.file.local_file_handler import LocalFileHandler
from src.env.resource.run.local_run_handler import LocalRunHandler
from src.operations.di_container import DIContainer
from src.context.resolver.config_resolver import create_config_root_from_dict

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
    root = create_config_root_from_dict(env_json)
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=env_json,
        resolver=root
    )
    file_handler = LocalFileHandler(env_context)
    run_handler = LocalRunHandler(env_context)
    controller = EnvResourceController(env_context, file_handler, run_handler)
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
    root = create_config_root_from_dict(env_json)
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=env_json,
        resolver=root
    )
    from src.env.resource.utils.path_utils import get_source_file_name
    # source_file_nameが存在しない場合、例外が発生する
    with pytest.raises(ValueError):
        get_source_file_name(env_context.resolver, env_context.language)

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
    root = create_config_root_from_dict(env_json)
    env_context = ExecutionContext(
        command_type="run",
        language="python",
        contest_name="abc001",
        problem_name="a",
        env_type="local",
        env_json=env_json,
        resolver=root
    )
    from src.env.resource.utils.path_utils import get_source_file_name
    # source_file_nameが正常に取得できることを確認
    result = get_source_file_name(env_context.resolver, env_context.language)
    assert result is not None, "source_file_name must not be None! env_jsonにsource_file_nameがありません" 