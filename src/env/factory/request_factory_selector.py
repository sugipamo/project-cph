from src.operations.di_container import DIContainer
from src.env.factory.shell_command_request_factory import ShellCommandRequestFactory
from src.env.factory.docker_command_request_factory import DockerCommandRequestFactory
from src.env.factory.copy_command_request_factory import CopyCommandRequestFactory
from src.env.factory.oj_command_request_factory import OjCommandRequestFactory
from src.env.factory.remove_command_request_factory import RemoveCommandRequestFactory
from src.env.factory.build_command_request_factory import BuildCommandRequestFactory
from src.env.factory.python_command_request_factory import PythonCommandRequestFactory
from src.env.factory.mkdir_command_request_factory import MkdirCommandRequestFactory
from src.env.factory.touch_command_request_factory import TouchCommandRequestFactory
from src.env.factory.rmtree_command_request_factory import RmtreeCommandRequestFactory
from src.env.factory.move_command_request_factory import MoveCommandRequestFactory
from src.env.factory.movetree_command_request_factory import MoveTreeCommandRequestFactory

class RequestFactorySelector:

    @classmethod
    def get_factory_for_step_type(cls, step_type: str, controller, operations: DIContainer):
        """
        step_typeに基づいて適切なファクトリーを返す
        """
        env_type = controller.env_context.env_type
        if step_type == "shell":
            if env_type and env_type.lower() == "docker":
                return operations.resolve("DockerCommandRequestFactory")(controller)
            else:
                return operations.resolve("ShellCommandRequestFactory")(controller)
        elif step_type == "copy":
            return operations.resolve("CopyCommandRequestFactory")(controller)
        elif step_type == "oj":
            DockerRequestClass = operations.resolve("DockerRequest")
            DockerOpTypeClass = operations.resolve("DockerOpType")
            return operations.resolve("OjCommandRequestFactory")(controller, DockerRequestClass, DockerOpTypeClass)
        elif step_type == "remove":
            return operations.resolve("RemoveCommandRequestFactory")(controller)
        elif step_type == "build":
            return operations.resolve("BuildCommandRequestFactory")(controller)
        elif step_type == "python":
            return operations.resolve("PythonCommandRequestFactory")(controller)
        elif step_type == "mkdir":
            return operations.resolve("MkdirCommandRequestFactory")(controller)
        elif step_type == "touch":
            return operations.resolve("TouchCommandRequestFactory")(controller)
        elif step_type == "rmtree":
            return operations.resolve("RmtreeCommandRequestFactory")(controller)
        elif step_type == "move":
            return operations.resolve("MoveCommandRequestFactory")(controller)
        elif step_type == "movetree":
            return operations.resolve("MoveTreeCommandRequestFactory")(controller)
        else:
            raise KeyError(f"Unknown step type: {step_type}")
    
 