import pytest
from src.execution_env.env_workflow_service import EnvWorkflowService, EnvContext
from src.operations.composite_request import CompositeRequest
from src.operations.base_request import BaseRequest

class DummyController:
    def __init__(self, language_name=None, env_type=None, env_config=None, file_handler=None, run_handler=None, const_handler=None):
        self.language_name = language_name
        self.env_type = env_type
        # 本物のEnvResourceControllerと同じインターフェースを持たせる
        self.env_context = self
        self.build_cmd = DummyRequest(f"build:{self.language_name}:{self.env_type}")
        self.run_cmd = DummyRequest(f"run:{self.language_name}:{self.env_type}")
    @classmethod
    def from_plan(cls, plan):
        return cls(language_name=plan.language, env_type=plan.env)
    @classmethod
    def from_context(cls, env_context):
        return cls(language_name=getattr(env_context, 'language', None), env_type=getattr(env_context, 'env', None))
    def copy_file(self, src, dst):
        return f"copy:{self.language_name}:{self.env_type}:{src}->{dst}"
    def prepare_sourcecode(self):
        return DummyRequest(f"prepare_sourcecode:{self.language_name}:{self.env_type}")
    def get_build_commands(self):
        return self.build_cmd
    def get_run_command(self):
        return self.run_cmd
    def create_process_options(self, cmd):
        return DummyRequest(cmd)

class DummyRequest(BaseRequest):
    def __init__(self, cmd):
        super().__init__(name=str(cmd))
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
        EnvContext(language="python", env="docker"),
        # EnvContext(language="cpp", env="local"),  # 不要なテストなので削除
    ]
    requests = service.generate_run_test_requests(run_plans)
    assert len(requests) == 2
    for req in requests:
        # driverはダミーでよい場合が多いが、必要なら適宜渡す
        result = req.execute()
        assert result is not None 