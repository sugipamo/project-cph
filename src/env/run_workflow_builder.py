from src.operations.composite.composite_request import CompositeRequest
from src.env.request_factory import create_requests_from_run_steps
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
        """
        requests = []
        # docker環境ならダミーoj stepを先頭に追加
        if self.controller.env_context.env_type.lower() == "docker":
            from src.env.step.run_step_oj import OjRunStep
            dummy_oj_step = OjRunStep(type="oj", cmd=["true"])
            run_steps = [dummy_oj_step] + list(run_steps)
        # 1. 必要ならビルドrequestを先頭に追加
        if self.needs_docker_build(run_steps):
            build_req = self.create_docker_build_request()
            requests.append(build_req)
        # 2. 各run_stepからrequest生成
        step_requests = create_requests_from_run_steps(self.controller, run_steps, self.operations)
        # step_requestsがCompositeRequestなら展開、単体ならそのまま
        if isinstance(step_requests, CompositeRequest):
            requests.extend(step_requests.requests)
        else:
            requests.append(step_requests)
        return CompositeRequest.make_composite_request(requests)

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

    def create_docker_build_request(self) -> object:
        """
        docker build用のDockerRequestを生成（operationsからクラスを解決）
        """
        image_name = self.controller.const_handler.image_name
        temp_path = str(self.controller.const_handler.contest_temp_path)
        dockerfile_text = self.controller.const_handler.dockerfile_text
        if not os.path.exists(temp_path):
            os.makedirs(temp_path, exist_ok=True)
        DockerRequest = self.operations.resolve("DockerRequest")
        DockerOpType = self.operations.resolve("DockerOpType")
        return DockerRequest(
            DockerOpType.BUILD,
            image=image_name,
            options={"f": "-", "t": image_name, "inputdata": dockerfile_text},
            command=temp_path
        ) 