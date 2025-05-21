from src.execution_env.resource_handler.file_handler.docker_file_handler import DockerFileHandler
from src.execution_env.resource_handler.file_handler.local_file_handler import LocalFileHandler
from src.execution_env.resource_handler.run_handler.local_run_handler import LocalRunHandler
from src.execution_env.resource_handler.run_handler.docker_run_handler import DockerRunHandler
from src.execution_env.resource_handler.env_utils.const_handler import ConstHandler
from src.operations.di_container import DIContainer
from src.execution_env.env_resource_controller import EnvResourceController

class EnvResourceControllerFactory:
    @staticmethod
    def create(env_context):
        """
        EnvContextからEnvResourceControllerを生成するファクトリメソッド。
        DIセットアップもここで行う。
        """
        container = DIContainer()
        container.register("ConstHandler", lambda: ConstHandler(env_context))
        container.register("LocalRunHandler", lambda: LocalRunHandler(env_context, container.resolve("ConstHandler")))
        container.register("DockerRunHandler", lambda: DockerRunHandler(env_context, container.resolve("ConstHandler")))
        container.register("LocalFileHandler", lambda: LocalFileHandler(env_context, container.resolve("ConstHandler")))
        container.register("DockerFileHandler", lambda: DockerFileHandler(env_context, container.resolve("ConstHandler")))
        const_handler = container.resolve("ConstHandler")
        if env_context.env_type.lower() == "docker":
            run_handler = container.resolve("DockerRunHandler")
            file_handler = container.resolve("DockerFileHandler")
        else:
            run_handler = container.resolve("LocalRunHandler")
            file_handler = container.resolve("LocalFileHandler")
        return EnvResourceController(env_context, file_handler, run_handler, const_handler) 