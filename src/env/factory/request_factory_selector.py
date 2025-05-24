from src.env.step.run_step_shell import ShellRunStep
from src.env.step.run_step_copy import CopyRunStep
from src.env.step.run_step_oj import OjRunStep
from src.env.step.run_step_remove import RemoveRunStep
from src.env.step.run_step_build import BuildRunStep
from src.env.step.run_step_python import PythonRunStep
from src.env.step.run_step_mkdir import MkdirRunStep
from src.env.step.run_step_touch import TouchRunStep
from src.env.step.run_step_rmtree import RmtreeRunStep
from src.env.step.run_step_move import MoveRunStep
from src.env.step.run_step_movetree import MoveTreeRunStep
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
    FACTORY_MAP = {
        "shell": ShellCommandRequestFactory,
        "docker_shell": DockerCommandRequestFactory,
        "copy": CopyCommandRequestFactory,
        "oj": OjCommandRequestFactory,
        "python": PythonCommandRequestFactory,
        "mkdir": MkdirCommandRequestFactory,
        "touch": TouchCommandRequestFactory,
        "test": None,
        "rmtree": RmtreeCommandRequestFactory,
        "move": MoveCommandRequestFactory,
        "movetree": MoveTreeCommandRequestFactory,
    }

    @staticmethod
    def get_shell_factory(controller, operations: DIContainer):
        env_type = controller.env_context.env_type
        if env_type.lower() == "docker":
            return operations.resolve("DockerCommandRequestFactory")(controller)
        else:
            return operations.resolve("ShellCommandRequestFactory")(controller)

    @classmethod
    def get_factory_for_step(cls, controller, step, operations: DIContainer):
        # stepにforce_env_typeがあればそれを優先
        env_type = getattr(step, 'force_env_type', None) or controller.env_context.env_type
        if isinstance(step, ShellRunStep):
            if env_type and env_type.lower() == "docker":
                return operations.resolve("DockerCommandRequestFactory")(controller)
            else:
                return operations.resolve("ShellCommandRequestFactory")(controller)
        elif isinstance(step, CopyRunStep):
            return operations.resolve("CopyCommandRequestFactory")(controller)
        elif isinstance(step, OjRunStep):
            DockerRequestClass = operations.resolve("DockerRequest")
            DockerOpTypeClass = operations.resolve("DockerOpType")
            return operations.resolve("OjCommandRequestFactory")(controller, DockerRequestClass, DockerOpTypeClass)
        elif isinstance(step, RemoveRunStep):
            return operations.resolve("RemoveCommandRequestFactory")(controller)
        elif isinstance(step, BuildRunStep):
            return operations.resolve("BuildCommandRequestFactory")(controller)
        elif isinstance(step, PythonRunStep):
            return operations.resolve("PythonCommandRequestFactory")(controller)
        elif isinstance(step, MkdirRunStep):
            return operations.resolve("MkdirCommandRequestFactory")(controller)
        elif isinstance(step, TouchRunStep):
            return operations.resolve("TouchCommandRequestFactory")(controller)
        elif isinstance(step, RmtreeRunStep):
            return operations.resolve("RmtreeCommandRequestFactory")(controller)
        elif isinstance(step, MoveRunStep):
            return operations.resolve("MoveCommandRequestFactory")(controller)
        elif isinstance(step, MoveTreeRunStep):
            return operations.resolve("MoveTreeCommandRequestFactory")(controller)
        else:
            factory_cls = cls.FACTORY_MAP[step.type]
            if not factory_cls:
                raise ValueError(f"Unknown or unsupported run type: {getattr(step, 'type', None)} (step={step})")
            return operations.resolve(factory_cls.__name__)(controller) 