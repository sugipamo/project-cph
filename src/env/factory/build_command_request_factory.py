from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_build import BuildRunStep
from src.operations.shell.shell_request import ShellRequest

class BuildCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, BuildRunStep):
            raise TypeError(f"BuildCommandRequestFactory expects BuildRunStep, got {type(run_step).__name__}")
        cmd = run_step.cmd or ["make"]  # デフォルトでmakeを実行（必要に応じて変更）
        return ShellRequest(cmd) 