from src.env.factory.base_command_request_factory import BaseCommandRequestFactory
from src.env.step.run_step_move import MoveRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class MoveCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, MoveRunStep):
            raise TypeError(f"MoveCommandRequestFactory expects MoveRunStep, got {type(run_step).__name__}")
        src = self.format_string(run_step.src)
        dst = self.format_string(run_step.dst)
        return FileRequest(FileOpType.MOVE, src, dst_path=dst) 