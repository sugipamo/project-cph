from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_remove import RemoveRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class RemoveCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step, const_handler=None):
        if not isinstance(run_step, RemoveRunStep):
            raise TypeError(f"RemoveCommandRequestFactory expects RemoveRunStep, got {type(run_step).__name__}")
        target = run_step.target
        if const_handler is not None:
            target = const_handler.parse(target)
        elif hasattr(self.controller, 'const_handler'):
            target = self.controller.const_handler.parse(target)
        return FileRequest(FileOpType.REMOVE, target) 