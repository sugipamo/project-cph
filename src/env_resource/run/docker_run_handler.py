from src.operations.docker.docker_request import DockerRequest, DockerOpType
from src.env_resource.run.base_run_handler import BaseRunHandler
from src.context.execution_context import ExecutionContext
from src.env_resource.utils.docker_naming import get_container_name

class DockerRunHandler(BaseRunHandler):
    def __init__(self, config: ExecutionContext, const_handler=None):
        super().__init__(config, const_handler)

    def create_process_options(self, cmd: list) -> DockerRequest:
        # DockerRequest(EXEC)を返す
        if self.config and hasattr(self.config, 'language'):
            dockerfile_text = getattr(self.config, 'dockerfile', None)
            container_name = get_container_name(self.config.language, dockerfile_text)
        else:
            container_name = "dummy_container"
        
        return DockerRequest(
            DockerOpType.EXEC,
            container=container_name,
            command=" ".join(cmd),
        ) 