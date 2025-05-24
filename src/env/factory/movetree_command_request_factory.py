from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_movetree import MoveTreeRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class MoveTreeCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, MoveTreeRunStep):
            raise TypeError(f"MoveTreeCommandRequestFactory expects MoveTreeRunStep, got {type(run_step).__name__}")
        src = self.controller.const_handler.parse(run_step.src)
        dst = self.controller.const_handler.parse(run_step.dst)
        return FileRequest(FileOpType.MOVE, src, dst_path=dst) 