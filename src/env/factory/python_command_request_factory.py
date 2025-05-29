from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_python import PythonRunStep
from src.operations.python.python_request import PythonRequest

class PythonCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, PythonRunStep):
            raise TypeError(f"PythonCommandRequestFactory expects PythonRunStep, got {type(run_step).__name__}")
        code_or_file = [self.format_string(str(arg)) for arg in run_step.cmd]
        cwd = self.format_string(run_step.cwd) if getattr(run_step, 'cwd', None) else None
        show_output = getattr(run_step, 'show_output', True)
        return PythonRequest(code_or_file, cwd=cwd, show_output=show_output) 