from src.execution_env.command_factory.base_command_request_factory import BaseCommandRequestFactory
from src.execution_env.run_step.run_step_shell import ShellRunStep
from src.operations.shell.shell_request import ShellRequest

class ShellCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, ShellRunStep):
            raise TypeError(f"ShellCommandRequestFactory expects ShellRunStep, got {type(run_step).__name__}")
        cmd = [self.controller.const_handler.parse(arg) for arg in run_step.cmd]
        return ShellRequest(cmd) 