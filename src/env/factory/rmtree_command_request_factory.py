from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_rmtree import RmtreeRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class RmtreeCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, RmtreeRunStep):
            raise TypeError(f"RmtreeCommandRequestFactory expects RmtreeRunStep, got {type(run_step).__name__}")
        target = self.controller.const_handler.parse(run_step.target)
        return FileRequest(FileOpType.RMTREE, target) 