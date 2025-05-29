from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_mkdir import MkdirRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class MkdirCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, MkdirRunStep):
            raise TypeError(f"MkdirCommandRequestFactory expects MkdirRunStep, got {type(run_step).__name__}")
        target = self.format_string(run_step.target)
        return FileRequest(FileOpType.MKDIR, target) 