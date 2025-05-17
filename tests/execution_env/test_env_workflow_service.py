import pytest
from src.execution_env.env_workflow_service import EnvWorkflowService, RunPlan
from src.operations.composite_request import CompositeRequest

class DummyController:
    def __init__(self, language_name=None, env_type=None, env_config=None, file_handler=None, run_handler=None, const_handler=None):
        self.language_name = language_name
        self.env_type = env_type
    def copy_file(self, src, dst):
        return f"copy:{self.language_name}:{self.env_type}:{src}->{dst}"
    def prepare_sourcecode(self):
        return f"prepare_sourcecode:{self.language_name}:{self.env_type}"
    def get_build_commands(self):
        return [["echo", f"build:{self.language_name}:{self.env_type}"]]
    def get_run_command(self):
        return ["echo", f"run:{self.language_name}:{self.env_type}"]
    def create_process_options(self, cmd):
        return DummyRequest(cmd)

class DummyRequest:
    def __init__(self, cmd):
        self.cmd = cmd
    def execute(self, driver=None):
        return f"executed:{self.cmd}:{driver}"

# DI用にEnvResourceControllerをモック化
import src.execution_env.env_workflow_service as workflow_mod

def test_generate_requests(monkeypatch):
    # EnvResourceControllerをダミーに差し替え
    monkeypatch.setattr(workflow_mod, "EnvResourceController", DummyController)
    service = EnvWorkflowService()
    run_plans = [
        RunPlan(language="python", env="docker", count=2),
        RunPlan(language="cpp", env="local", count=1),
    ]
    requests = service.generate_requests(run_plans)
    assert len(requests) == 3
    assert all(isinstance(r, CompositeRequest) for r in requests)
    # 中身の確認
    req0 = requests[0].requests[0]
    assert req0 == "copy:python:docker:src->dst"
    req2 = requests[2].requests[0]
    assert req2 == "copy:cpp:local:src->dst" 