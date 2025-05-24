from src.operations.composite.composite_request import CompositeRequest
from src.env.factory.request_factory import create_requests_from_run_steps
from src.env.step.run_step_shell import ShellRunStep
from src.env.step.run_step_oj import OjRunStep
from src.operations.di_container import DIContainer
from src.env.types import EnvResourceController, RunSteps, CompositeRequest
import os

class RunWorkflowBuilder:
    def __init__(self, controller: EnvResourceController, operations: DIContainer):
        self.controller = controller
        self.operations = operations

    @classmethod
    def from_controller(cls, controller: EnvResourceController, operations: DIContainer) -> 'RunWorkflowBuilder':
        """
        controllerとoperationsからRunWorkflowBuilderを生成
        """
        return cls(controller, operations)

    def build(self, run_steps: RunSteps) -> CompositeRequest:
        """
        run_steps: RunSteps型
        最低限のリクエストのみ生成（事前準備リクエストは追加しない）
        """
        # 事前準備（ダミーoj stepやdocker buildリクエスト）は追加しない
        step_requests = create_requests_from_run_steps(self.controller, run_steps, self.operations)
        if isinstance(step_requests, CompositeRequest):
            return step_requests
        else:
            return CompositeRequest.make_composite_request([step_requests])

    def needs_docker_build(self, run_steps: RunSteps) -> bool:
        """
        run_steps内にDockerRequestが必要なstep（docker環境のshell/oj等）が含まれていればTrue
        """
        env_type = self.controller.env_context.env_type.lower()
        if env_type != "docker":
            return False
        # shell/oj系stepが1つでもあればビルド必要とみなす（仮実装）
        for step in run_steps:
            if isinstance(step, (ShellRunStep, OjRunStep)):
                return True
        return False

    def create_docker_build_request(self, dockerfile_text) -> object:
        """
        docker build用のDockerRequestを生成（operationsからクラスを解決）
        """
        image_name = self.controller.const_handler.image_name
        temp_path = str(self.controller.const_handler.contest_temp_path)
        if not os.path.exists(temp_path):
            os.makedirs(temp_path, exist_ok=True)
        DockerRequest = self.operations.resolve("DockerRequest")
        DockerOpType = self.operations.resolve("DockerOpType")
        return DockerRequest(
            DockerOpType.BUILD,
            image=image_name,
            options={"f": "-", "t": image_name},
            command=temp_path,
            dockerfile_text=dockerfile_text
        ) 