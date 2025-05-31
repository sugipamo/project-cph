from src.env_resource.run.base_run_handler import BaseRunHandler
from src.operations.shell.shell_request import ShellRequest
from src.context.execution_context import ExecutionContext

class LocalRunHandler(BaseRunHandler):
    def __init__(self, config: ExecutionContext, const_handler=None):
        super().__init__(config, const_handler)
    def create_process_options(self, cmd: list) -> ShellRequest:
        # コマンド配列内の各要素に対して変数展開
        return ShellRequest(cmd) 