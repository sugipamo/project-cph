from src.execution_env.run_step.run_step_shell import ShellRunStep
from src.execution_env.run_step.run_step_copy import CopyRunStep
from src.execution_env.run_step.run_step_oj import OjRunStep
from src.operations.di_container import DIContainer
from src.execution_env.command_factory.shell_command_request_factory import ShellCommandRequestFactory
from src.execution_env.command_factory.docker_command_request_factory import DockerCommandRequestFactory
from src.execution_env.command_factory.copy_command_request_factory import CopyCommandRequestFactory
from src.execution_env.command_factory.oj_command_request_factory import OjCommandRequestFactory

class RequestFactorySelector:
    FACTORY_MAP = {
        "shell": ShellCommandRequestFactory,
        "docker_shell": DockerCommandRequestFactory,
        "copy": CopyCommandRequestFactory,
        "oj": OjCommandRequestFactory,
        "test": None,
    }

    @staticmethod
    def get_shell_factory(controller, di_container: DIContainer):
        env_type = getattr(controller.env_context, "env_type", "local")
        if env_type.lower() == "docker":
            return di_container.resolve("DockerCommandRequestFactory")(controller)
        else:
            return di_container.resolve("ShellCommandRequestFactory")(controller)

    @classmethod
    def get_factory_for_step(cls, controller, step, di_container: DIContainer):
        if isinstance(step, ShellRunStep):
            return cls.get_shell_factory(controller, di_container)
        elif isinstance(step, CopyRunStep):
            return di_container.resolve("CopyCommandRequestFactory")(controller)
        elif isinstance(step, OjRunStep):
            return di_container.resolve("OjCommandRequestFactory")(controller)
        else:
            factory_cls = cls.FACTORY_MAP.get(getattr(step, "type", None))
            if not factory_cls:
                raise ValueError(f"Unknown or unsupported run type: {getattr(step, 'type', None)} (step={step})")
            return di_container.resolve(factory_cls.__name__)(controller) 