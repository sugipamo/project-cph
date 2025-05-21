from src.execution_env.base_command_request_factory import BaseCommandRequestFactory
from src.execution_env.run_step_copy import CopyRunStep
from src.operations.file.file_request import FileRequest, FileOpType

class CopyCommandRequestFactory(BaseCommandRequestFactory):
    def create_request(self, run_step):
        if not isinstance(run_step, CopyRunStep):
            raise TypeError(f"CopyCommandRequestFactory expects CopyRunStep, got {type(run_step).__name__}")
        if len(run_step.cmd) < 2:
            raise ValueError("CopyRunStep: cmdにはsrcとdstの2つが必要です")
        src = self.controller.const_handler.parse(run_step.cmd[0])
        dst = self.controller.const_handler.parse(run_step.cmd[1])
        return FileRequest(FileOpType.COPY, src, dst_path=dst) 