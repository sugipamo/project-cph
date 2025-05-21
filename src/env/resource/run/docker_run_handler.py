from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.env.resource.run.base_run_handler import BaseRunHandler
from src.context.execution_context import ExecutionContext

class DockerRunHandler(BaseRunHandler):
    def __init__(self, config: ExecutionContext, const_handler):
        super().__init__(config, const_handler)

    def create_process_options(self, cmd: list) -> DockerRequest:
        # DockerRequest(EXEC)を返す
        return DockerRequest(
            DockerOpType.EXEC,
            container=self.const_handler.container_name,
            command=" ".join(cmd),
        ) 